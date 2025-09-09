# Django REST Framework Backend

Proyecto backend desarrollado con Django 4.2 y Django REST Framework, configurado con PostgreSQL y gestión de dependencias mediante pip-tools.

## 🚀 Configuración Inicial

### 1. Clonar y preparar el entorno

```bash
# Clonar el repositorio
git clone <repository-url>
cd ai-software-development

# Crear entorno virtual
python3 -m venv .env
source .env/bin/activate  # En macOS/Linux
# .env\Scripts\activate     # En Windows

# Instalar pip-tools
pip install pip-tools

# Compilar e instalar dependencias
pip-compile requirements.in
pip-sync requirements.txt
```

### 2. Configurar variables de entorno

Copia el archivo de ejemplo y configura tus variables:

```bash
cp env.example .env
```

Edita el archivo `.env` con tus configuraciones:

```env
# Database Configuration
DB_NAME=django_db
DB_USER=django_user
DB_PASSWORD=django_password
DB_HOST=localhost
DB_PORT=5432

# Django Configuration
DEBUG=True
SECRET_KEY=tu-clave-secreta-aqui
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 3. Levantar PostgreSQL con Docker

```bash
# Levantar contenedor de PostgreSQL
docker-compose up -d

# Verificar que está funcionando
docker-compose ps
```

### 4. Ejecutar migraciones y servidor

```bash
# Activar entorno virtual
source .env/bin/activate

# Verificar configuración
python3 manage.py check

# Ejecutar migraciones
python3 manage.py migrate

# Crear superusuario (opcional)
python3 manage.py createsuperuser

# Levantar servidor de desarrollo
python3 manage.py runserver
```

## 📁 Estructura del Proyecto

```
ai-software-development/
├── .env/                   # Entorno virtual (ignorado en git)
├── config/                 # Configuración principal de Django
│   ├── __init__.py
│   ├── settings.py         # Configuraciones del proyecto
│   ├── urls.py            # URLs principales
│   ├── wsgi.py
│   └── asgi.py
├── core/                   # App principal del proyecto
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py          # Modelos de datos
│   ├── views.py           # Vistas/ViewSets
│   ├── urls.py            # URLs de la app
│   └── tests.py
├── docker-compose.yml      # PostgreSQL container
├── env.example            # Ejemplo de variables de entorno
├── requirements.in         # Dependencias directas
├── requirements.txt        # Dependencias compiladas (generado)
├── requirements-dev.in     # Dependencias de desarrollo
├── manage.py              # Comando principal de Django
└── README.md              # Este archivo
```

## 🛠️ Gestión de Dependencias con pip-tools

### Agregar nueva dependencia

```bash
# 1. Agregar al requirements.in
echo "nueva-libreria>=1.0" >> requirements.in

# 2. Compilar dependencias
pip-compile requirements.in

# 3. Sincronizar entorno
pip-sync requirements.txt
```

### Actualizar dependencias

```bash
# Actualizar todas las dependencias
pip-compile --upgrade requirements.in
pip-sync requirements.txt

# Actualizar solo una dependencia específica
pip-compile --upgrade-package django requirements.in
pip-sync requirements.txt
```

### Dependencias de desarrollo

```bash
# Compilar dependencias de desarrollo
pip-compile requirements-dev.in

# Instalar dependencias de desarrollo
pip-sync requirements-dev.txt
```

## 🐳 Docker Commands

```bash
# Levantar PostgreSQL
docker-compose up -d

# Ver logs de PostgreSQL
docker-compose logs postgres

# Parar PostgreSQL
docker-compose down

# Parar y eliminar volúmenes (⚠️ elimina datos)
docker-compose down -v
```

## 🔧 Comandos Django Útiles

```bash
# Verificar configuración
python3 manage.py check

# Crear migraciones
python3 manage.py makemigrations

# Aplicar migraciones
python3 manage.py migrate

# Crear superusuario
python3 manage.py createsuperuser

# Abrir shell de Django
python3 manage.py shell

# Ejecutar tests
python3 manage.py test

# Recopilar archivos estáticos (producción)
python3 manage.py collectstatic
```

## 📋 Checklist de Verificación

- [ ] ✅ Entorno virtual creado y activado
- [ ] ✅ Dependencias instaladas con pip-sync
- [ ] ✅ PostgreSQL funcionando (docker-compose up -d)
- [ ] ✅ Variables de entorno configuradas (.env)
- [ ] ✅ Migraciones aplicadas (python3 manage.py migrate)
- [ ] ✅ Servidor funcionando (python3 manage.py runserver)
- [ ] ✅ Admin accesible en http://127.0.0.1:8000/admin/
- [ ] ✅ API base accesible en http://127.0.0.1:8000/api/

## 🚀 Siguientes Pasos

1. **Crear modelos** en `core/models.py`
2. **Crear serializers** en `core/serializers.py`
3. **Crear ViewSets** en `core/views.py`
4. **Registrar URLs** en `core/urls.py`
5. **Agregar tests** en `core/tests.py`

## 🔗 URLs Importantes

- **Admin**: http://127.0.0.1:8000/admin/
- **API Base**: http://127.0.0.1:8000/api/
- **DRF Browsable API**: Disponible en endpoints de API

## 📚 Tecnologías Utilizadas

- **Django 4.2**: Framework web principal
- **Django REST Framework 3.16**: API REST
- **PostgreSQL 15**: Base de datos
- **pip-tools**: Gestión de dependencias
- **Docker Compose**: Contenedor de PostgreSQL
- **python-decouple**: Variables de entorno
