
import os
import urllib.request
import urllib.error
import urllib.parse

from config import Config
from app.database import get_db


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class CloudArchivalController:
    """Manage local staging and Hadoop HDFS archiving."""

    def __init__(self):
        self.hdfs_enabled = Config.HDFS_ENABLED
        self.namenode_host = Config.HDFS_NAMENODE_HOST
        self.namenode_port = Config.HDFS_NAMENODE_PORT
        self.hdfs_user = Config.HDFS_USER
        self.archive_dir = Config.HDFS_ARCHIVE_DIR.rstrip("/")
        self.webhdfs_base_url = (
            f"http://{self.namenode_host}:{self.namenode_port}/webhdfs/v1"
        )
        self.opener = urllib.request.build_opener(NoRedirectHandler())

    def _request(self, url, data=None, method="GET", timeout=10):
        request = urllib.request.Request(
            url, data=data, method=method,
            headers={"User-Agent": "AttendCloud-Controller/1.0"},
        )
        try:
            return self.opener.open(request, timeout=timeout)
        except urllib.error.HTTPError as exc:
            if exc.code in (301, 302, 307, 308):
                return exc
            raise

    def get_cluster_status(self):
        info = {
            "controller_name": Config.CLOUD_CONTROLLER_NAME,
            "controller_mode": Config.CLOUD_CONTROLLER_MODE,
            "controller_status": "Healthy & Online (LAN Primary Node)",
            "hdfs_enabled": self.hdfs_enabled,
            "namenode_endpoint": f"{self.namenode_host}:{self.namenode_port}",
            "hdfs_user": self.hdfs_user,
            "hdfs_status": "Not Configured (Local Staging Active)",
            "status_badge_class": "badge-warning",
            "is_hdfs_online": False,
            "details": "Reports are retained locally until HDFS is enabled.",
        }

        if not self.hdfs_enabled:
            return info

        query = urllib.parse.urlencode({
            "op": "GETFILESTATUS",
            "user.name": self.hdfs_user,
        })

        try:
            with urllib.request.urlopen(
                f"{self.webhdfs_base_url}/?{query}", timeout=5
            ) as response:
                if response.status == 200:
                    info.update({
                        "hdfs_status": "Connected (WebHDFS Online)",
                        "status_badge_class": "badge-success",
                        "is_hdfs_online": True,
                        "details": (
                            f"Successfully contacted NameNode at "
                            f"{self.namenode_host}:{self.namenode_port}."
                        ),
                    })
        except Exception as exc:
            info.update({
                "hdfs_status": "Offline / Connection Failed",
                "status_badge_class": "badge-danger",
                "details": f"WebHDFS connectivity check failed: {exc}",
            })

        return info

    def archive_report(self, filepath, filename, record_count, date_range=None):
        if not os.path.isfile(filepath):
            return {
                "success": False,
                "message": f"Source report '{filename}' was not found.",
            }

        file_size_bytes = os.path.getsize(filepath)
        db = get_db()

        if not self.hdfs_enabled:
            destination = f"file://{os.path.abspath(filepath)}"
            status = "Stored_Local"
            archive_type = "Local Staging"
            notes = "HDFS is disabled; report retained locally."
        else:
            target_path = f"{self.archive_dir}/{filename}"
            encoded_path = urllib.parse.quote(target_path, safe="/")

            try:
                # Ensure the HDFS archive directory exists with write permissions.
                mkdir_query = urllib.parse.urlencode({
                    "op": "MKDIRS",
                    "user.name": self.hdfs_user,
                    "permission": "777",
                })
                mkdir_request = urllib.request.Request(
                    f"{self.webhdfs_base_url}{self.archive_dir}?{mkdir_query}",
                    data=b"",
                    method="PUT",
                )
                try:
                    with urllib.request.urlopen(
                        mkdir_request, timeout=10
                    ) as response:
                        if response.status not in (200, 201):
                            raise RuntimeError(
                                f"MKDIRS returned HTTP {response.status}"
                            )
                except urllib.error.HTTPError as mkdir_err:
                    # If 403 occurs with configured user, try fallback user 'ndaav'
                    if mkdir_err.code == 403 and self.hdfs_user != "ndaav":
                        fallback_query = urllib.parse.urlencode({
                            "op": "MKDIRS",
                            "user.name": "ndaav",
                            "permission": "777",
                        })
                        fallback_req = urllib.request.Request(
                            f"{self.webhdfs_base_url}{self.archive_dir}?{fallback_query}",
                            data=b"",
                            method="PUT",
                        )
                        with urllib.request.urlopen(fallback_req, timeout=10) as fb_resp:
                            if fb_resp.status not in (200, 201):
                                raise RuntimeError(f"MKDIRS fallback returned HTTP {fb_resp.status}")
                    else:
                        raise

                # Ask the NameNode to create the destination file.
                create_query = urllib.parse.urlencode({
                    "op": "CREATE",
                    "overwrite": "true",
                    "user.name": self.hdfs_user,
                })
                create_url = (
                    f"{self.webhdfs_base_url}{encoded_path}?{create_query}"
                )

                with open(filepath, "rb") as source:
                    file_data = source.read()

                response = self._request(
                    create_url, data=b"", method="PUT", timeout=10
                )
                try:
                    redirect_location = response.headers.get("Location")
                    response_code = getattr(response, "code", response.status)
                    if response_code not in (200, 201, 301, 302, 307, 308):
                        raise RuntimeError(
                            f"NameNode returned HTTP {response_code}"
                        )
                finally:
                    response.close()

                if not redirect_location:
                    raise RuntimeError(
                        "NameNode did not provide a DataNode redirect."
                    )

                # Parse redirect location and prepare candidate DataNode endpoints
                parsed = urllib.parse.urlsplit(redirect_location)
                redirect_host = parsed.hostname or ""
                redirect_port = parsed.port or 9864

                candidate_hosts = []
                if self.namenode_host and self.namenode_host not in ("127.0.0.1", "localhost"):
                    candidate_hosts.append(self.namenode_host)
                # Primary reachable local endpoints
                candidate_hosts.extend(["127.0.0.1", "192.168.9.221"])
                if redirect_host and redirect_host not in candidate_hosts and not redirect_host.lower().endswith(".localdomain"):
                    candidate_hosts.append(redirect_host)

                # Preserve query parameters
                query_params = urllib.parse.parse_qs(parsed.query)
                query_params["op"] = ["CREATE"]
                query_params["user.name"] = [self.hdfs_user]
                encoded_qs = urllib.parse.urlencode(query_params, doseq=True)

                upload_succeeded = False
                last_upload_exc = None

                for host in candidate_hosts:
                    upload_url = urllib.parse.urlunsplit((
                        parsed.scheme,
                        f"{host}:{redirect_port}",
                        parsed.path,
                        encoded_qs,
                        "",
                    ))
                    upload_request = urllib.request.Request(
                        upload_url,
                        data=file_data,
                        method="PUT",
                        headers={"Content-Type": "application/octet-stream"},
                    )
                    try:
                        with urllib.request.urlopen(
                            upload_request, timeout=30
                        ) as up_response:
                            if up_response.status in (200, 201):
                                upload_succeeded = True
                                break
                            else:
                                raise RuntimeError(
                                    f"DataNode returned HTTP {up_response.status}"
                                )
                    except Exception as exc:
                        last_upload_exc = exc
                        continue

                if not upload_succeeded:
                    raise last_upload_exc or RuntimeError("All DataNode candidate endpoints failed.")

                destination = f"hdfs://{self.namenode_host}:9000{target_path}"
                status = "Synced_HDFS"
                archive_type = "HDFS Live"
                notes = f"Successfully uploaded report to HDFS: {target_path}"

            except Exception as exc:
                destination = f"file://{os.path.abspath(filepath)}"
                status = "Pending_HDFS_Config"
                archive_type = "Local Staging"
                notes = (
                    f"HDFS upload failed: {type(exc).__name__}: {exc}. "
                    "The local report remains available."
                )

        db.execute(
            """
            INSERT INTO archive_logs
            (filename, file_path, file_size_bytes, record_count, date_range,
             archive_type, hdfs_destination, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                filename, filepath, file_size_bytes, record_count,
                date_range, archive_type, destination, status, notes,
            ),
        )
        db.commit()

        return {
            "success": status in ("Synced_HDFS", "Stored_Local"),
            "mode": archive_type,
            "status": status,
            "filename": filename,
            "file_size_bytes": file_size_bytes,
            "destination": destination,
            "message": notes,
        }
