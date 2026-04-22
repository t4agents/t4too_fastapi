from fastapi.openapi.utils import get_openapi

def add_swagger_lock(app):
    original_openapi = app.openapi
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = original_openapi()
        openapi_schema["components"]["securitySchemes"] = {
            "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
        }
        openapi_schema["security"] = [{"bearerAuth": []}]
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    app.openapi = custom_openapi