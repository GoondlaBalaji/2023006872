from logging_middleware.app.logger import Log

result = Log(
    "backend",
    "info",
    "service",
    "Logging middleware initialized"
)

print(result)