import os
from flask import Flask, render_template
from config import Config
from app.database import init_app

def create_app(config_class=Config):
    """Application factory for AttendCloud SaaS."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize SQLite database & tables automatically
    init_app(app)

    # Register blueprints
    from app.routes.dashboard import dashboard_bp
    from app.routes.students import students_bp
    from app.routes.attendance import attendance_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)

    # Global context processor for template headers and footer
    @app.context_processor
    def inject_global_metadata():
        return {
            'app_title': 'AttendCloud',
            'app_tagline': 'LAN-Based SaaS Attendance Management System',
            'controller_name': Config.CLOUD_CONTROLLER_NAME,
            'hdfs_enabled': Config.HDFS_ENABLED
        }

    # Error handling
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', error_code=404, error_message="Page Not Found"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('base.html', error_code=500, error_message="Internal Server Error"), 500

    return app
