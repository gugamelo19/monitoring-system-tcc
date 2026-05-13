from pathlib import Path
from decouple import config
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-me")
DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost",
                       cast=lambda v: [s.strip() for s in v.split(",")])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",

    "apps.accounts",
    "apps.assets",
    "apps.events",
    "apps.anomalies",
    "apps.alerts",
    "apps.dashboard",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="monitoring-system-tcc-db"),
        "USER": config("DB_USER", default="postgres"),
        "PASSWORD": config("DB_PASSWORD", default="AS123as"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Bahia"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS — em produção, restringir explicitamente aos domínios do frontend.
CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=True, cast=bool)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    # NOTE: a paginação está desligada nesta versão para preservar a
    # compatibilidade do frontend, que consome listas como arrays JSON.
    # Para ativá-la em produção, adicionar:
    #   "DEFAULT_PAGINATION_CLASS":
    #       "rest_framework.pagination.PageNumberPagination",
    #   "PAGE_SIZE": 50,
    # e adaptar o frontend para ler "results" da resposta.
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# ============================================================
# Configurações do motor de detecção de anomalias.
#
# Os limiares abaixo são lidos pelo AnomalyDetectorService e
# podem ser sobrescritos via variáveis de ambiente, viabilizando
# a análise de sensibilidade (variação paramétrica dos limiares)
# sem necessidade de alterar código.
# ============================================================

DETECTOR_THRESHOLDS = {
    # HIGH_ICMP_RATE: dispara quando há mais de N eventos ICMP do mesmo
    # source_ip dentro de WINDOW_SECONDS.
    "ICMP_RATE_COUNT": config("ICMP_RATE_COUNT", default=20, cast=int),
    "ICMP_RATE_WINDOW_SECONDS": config(
        "ICMP_RATE_WINDOW_SECONDS", default=30, cast=int),

    # PORT_SCAN_SUSPECT: dispara quando há mais de N portas TCP destino
    # distintas do mesmo source_ip dentro de WINDOW_SECONDS.
    "PORT_SCAN_DISTINCT_PORTS": config(
        "PORT_SCAN_DISTINCT_PORTS", default=10, cast=int),
    "PORT_SCAN_WINDOW_SECONDS": config(
        "PORT_SCAN_WINDOW_SECONDS", default=60, cast=int),

    # DNS_QUERY_BURST: dispara quando há mais de N eventos DNS do mesmo
    # source_ip dentro de WINDOW_SECONDS.
    "DNS_BURST_COUNT": config("DNS_BURST_COUNT", default=30, cast=int),
    "DNS_BURST_WINDOW_SECONDS": config(
        "DNS_BURST_WINDOW_SECONDS", default=60, cast=int),

    # Janela de deduplicação: anomalias do mesmo tipo, no mesmo asset,
    # dentro deste intervalo são suprimidas como duplicatas.
    "DEDUPLICATION_WINDOW_SECONDS": config(
        "DEDUPLICATION_WINDOW_SECONDS", default=60, cast=int),

    # Duração padrão (em horas) da supressão automática quando um alerta
    # é marcado como FALSE_POSITIVE pelo operador.
    "FALSE_POSITIVE_SUPPRESS_HOURS": config(
        "FALSE_POSITIVE_SUPPRESS_HOURS", default=24, cast=int),
}
