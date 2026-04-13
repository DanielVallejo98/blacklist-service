# Blacklist Microservice — Guía Completa de Despliegue

Microservicio REST en Flask para gestión de lista negra global de emails.
Desplegado sobre **AWS Elastic Beanstalk** con **contenedor Docker** y **AWS RDS (PostgreSQL)**.

---

## Tabla de Contenidos
1. [Estructura del Proyecto](#estructura)
2. [Correr Localmente con Docker](#local)
3. [Configurar AWS RDS](#rds)
4. [Desplegar en AWS Elastic Beanstalk](#beanstalk)
5. [Estrategias de Despliegue](#estrategias)
6. [API Reference](#api)
7. [Token de Autorización](#token)

---

## 1. Estructura del Proyecto <a name="estructura"></a>

```
blacklist-service/
├── app.py                        # Entry point de Flask
├── config.py                     # Configuración (DB, JWT, token)
├── extensions.py                 # SQLAlchemy + Marshmallow
├── requirements.txt
├── Dockerfile
├── docker-compose.yml            # Para desarrollo local
├── Dockerrun.aws.json            # Para Elastic Beanstalk
├── .env.example
├── .gitignore
├── .ebextensions/
│   └── 01_env.config             # Variables de entorno en Beanstalk
├── models/
│   └── blacklist.py              # Modelo BlacklistEntry
├── routes/
│   ├── blacklist_routes.py       # POST /blacklists y GET /blacklists/<email>
│   └── health_routes.py          # GET /health
└── schemas/
    └── blacklist_schema.py       # Validación y serialización
```

---

## 2. Correr Localmente con Docker <a name="local"></a>

### Prerequisitos
- Docker Desktop instalado y corriendo
- Git instalado

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/blacklist-service.git
cd blacklist-service

# 2. Levantar los contenedores (API + PostgreSQL)
docker-compose up --build

# 3. Verificar que todo funciona
curl http://localhost:5000/health
# Respuesta esperada: {"status": "healthy", "database": "ok", "service": "blacklist-api"}
```

La API queda disponible en `http://localhost:5000`

---

## 3. Configurar AWS RDS <a name="rds"></a>

### Paso 1: Crear la instancia RDS

1. Ingresar a la **consola de AWS** → buscar **RDS**
2. Clic en **"Create database"**
3. Configurar:
   - **Engine**: PostgreSQL
   - **Version**: PostgreSQL 15.x
   - **Templates**: Free tier (para pruebas) o Production
   - **DB instance identifier**: `blacklist-db`
   - **Master username**: `postgres`
   - **Master password**: (anotar esta contraseña, la necesitarás)
   - **DB instance class**: `db.t3.micro`
   - **Storage**: 20 GB gp2
4. En **"Connectivity"**:
   - **VPC**: Default VPC
   - **Public access**: **Yes** (necesario para que Beanstalk se conecte)
   - **VPC security group**: crear uno nuevo llamado `blacklist-rds-sg`
5. En **"Additional configuration"**:
   - **Initial database name**: `blacklist_db`
6. Clic en **"Create database"** → esperar ~5 minutos

### Paso 2: Configurar el Security Group de RDS

1. Ir a **EC2 → Security Groups** → buscar `blacklist-rds-sg`
2. **Inbound rules** → **Edit inbound rules**
3. Agregar regla:
   - **Type**: PostgreSQL
   - **Port**: 5432
   - **Source**: `0.0.0.0/0` (para pruebas) o el SG de Beanstalk
4. Guardar

### Paso 3: Anotar el Endpoint

En la consola de RDS → tu instancia → sección **"Connectivity & security"**:
```
Endpoint: blacklist-db.xxxxxxxxx.us-east-1.rds.amazonaws.com
Port:     5432
```

---

## 4. Desplegar en AWS Elastic Beanstalk <a name="beanstalk"></a>

### Paso 1: Instalar EB CLI

```bash
pip install awsebcli
eb --version
```

### Paso 2: Configurar credenciales AWS

```bash
aws configure
# AWS Access Key ID: (pegar tu key de AWS Academy)
# AWS Secret Access Key: (pegar tu secret)
# Default region: us-east-1
# Default output format: json
```

### Paso 3: Inicializar Elastic Beanstalk

```bash
cd blacklist-service
eb init

# Responder:
# - Region: us-east-1
# - Application name: blacklist-service
# - Platform: Docker
# - Platform version: (la más reciente)
# - SSH: Yes (para poder conectarte a las instancias)
```

### Paso 4: Crear el entorno con Auto Scaling

```bash
eb create blacklist-env \
  --instance-type t3.small \
  --min-instances 3 \
  --max-instances 6 \
  --elb-type application
```

### Paso 5: Configurar variables de entorno

En la **consola de AWS → Elastic Beanstalk → blacklist-env → Configuration → Software → Edit**:

Agregar estas variables de entorno:

| Variable       | Valor                                        |
|----------------|----------------------------------------------|
| DB_USER        | postgres                                     |
| DB_PASSWORD    | (tu contraseña de RDS)                       |
| DB_HOST        | (endpoint de RDS, sin puerto)                |
| DB_PORT        | 5432                                         |
| DB_NAME        | blacklist_db                                 |
| JWT_SECRET_KEY | (una cadena aleatoria larga y segura)        |
| STATIC_TOKEN   | (el token que usarás en Postman)             |

**O** desde la terminal:

```bash
eb setenv \
  DB_USER=postgres \
  DB_PASSWORD=TU_PASSWORD \
  DB_HOST=blacklist-db.xxxxxxx.us-east-1.rds.amazonaws.com \
  DB_PORT=5432 \
  DB_NAME=blacklist_db \
  JWT_SECRET_KEY=mi-super-clave-secreta-2024 \
  STATIC_TOKEN=mi-token-estatico-2024
```

### Paso 6: Configurar Health Check

En **Configuration → Load balancer → Processes → default → Edit**:
- **Health check path**: `/health`
- **HTTP code**: `200`
- **Interval**: 30 segundos
- **Timeout**: 10 segundos
- **Unhealthy threshold**: 5

### Paso 7: Desplegar

```bash
eb deploy
# Esperar ~3-5 minutos
```

### Paso 8: Verificar

```bash
eb open   # Abre la URL en el navegador
eb status # Ver estado del entorno
```

URL del entorno:
```
http://blacklist-env.xxxxxxxx.us-east-1.elasticbeanstalk.com
```

---

## 5. Estrategias de Despliegue <a name="estrategias"></a>

Para cambiar la estrategia, ir a **Elastic Beanstalk → blacklist-env → Configuration → Rolling updates and deployments → Edit**.

### Estrategia 1: All at Once
- **Configuración**: Deployment policy = `All at once`
- **Qué hace**: Despliega en TODAS las instancias al mismo tiempo
- **Ventaja**: Más rápido
- **Desventaja**: Downtime durante el despliegue
- **Instancias afectadas**: Todas las existentes
- **Cuándo usar**: Entornos de desarrollo

### Estrategia 2: Rolling
- **Configuración**: Deployment policy = `Rolling`, Batch size = `1` instancia
- **Qué hace**: Actualiza de a 1 instancia a la vez, manteniendo el resto activo
- **Ventaja**: Sin downtime completo
- **Desventaja**: Versiones mixtas durante el proceso
- **Instancias afectadas**: Las existentes, una por una

### Estrategia 3: Rolling with Additional Batch
- **Configuración**: Deployment policy = `Rolling with additional batch`, Batch size = `1`
- **Qué hace**: Crea una instancia NUEVA primero, luego va rotando las viejas
- **Ventaja**: Siempre mantiene la capacidad completa
- **Desventaja**: Costo adicional temporal
- **Instancias afectadas**: Se crean nuevas + se actualizan las existentes

### Estrategia 4: Immutable
- **Configuración**: Deployment policy = `Immutable`
- **Qué hace**: Crea un NUEVO grupo completo de instancias, luego elimina las viejas
- **Ventaja**: Rollback instantáneo, cero downtime
- **Desventaja**: Costo doble temporal, más lento
- **Instancias afectadas**: Solo las nuevas; las viejas se eliminan al final

### Estrategia 5 (bonus): Traffic Splitting
- **Configuración**: Deployment policy = `Traffic splitting`, porcentaje inicial = `10%`
- **Qué hace**: Envía un porcentaje del tráfico a la nueva versión (canary deployment)
- **Ventaja**: Prueba en producción con tráfico real mínimo
- **Desventaja**: Requiere ALB (Application Load Balancer)

---

## 6. API Reference <a name="api"></a>

### POST /blacklists
Agrega un email a la lista negra.

**Headers:**
```
Authorization: Bearer mi-token-estatico-2024
Content-Type:  application/json
```

**Body:**
```json
{
  "email": "usuario@ejemplo.com",
  "app_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "blocked_reason": "Spam reiterado"
}
```

**Respuestas:**
| Código | Descripción |
|--------|-------------|
| 201    | Email agregado exitosamente |
| 400    | Datos inválidos o faltantes |
| 401    | Token inválido o ausente |
| 409    | El email ya está en la lista negra |

---

### GET /blacklists/{email}
Consulta si un email está en la lista negra.

**Headers:**
```
Authorization: Bearer mi-token-estatico-2024
```

**Respuesta exitosa (en lista negra):**
```json
{
  "is_blacklisted": true,
  "email": "usuario@ejemplo.com",
  "blocked_reason": "Spam reiterado",
  "app_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-15T10:30:00"
}
```

**Respuesta exitosa (no en lista negra):**
```json
{
  "is_blacklisted": false,
  "email": "usuario@ejemplo.com",
  "blocked_reason": null
}
```

---

### GET /health
Health check para AWS Elastic Beanstalk.

**Respuesta:**
```json
{
  "status": "healthy",
  "database": "ok",
  "service": "blacklist-api"
}
```

---

## 7. Token de Autorización <a name="token"></a>

Por simplicidad, el token es **estático** y se configura mediante la variable de entorno `STATIC_TOKEN`.

Para usar la API incluir en cada request:
```
Authorization: Bearer mi-token-estatico-2024
```

En Postman: `Authorization` → `Type: Bearer Token` → pegar el valor del token.

---

## Comandos útiles de EB CLI

```bash
eb status          # Estado del entorno
eb health          # Health de las instancias
eb logs            # Ver logs de la aplicación
eb open            # Abrir URL en el navegador
eb deploy          # Desplegar nueva versión
eb terminate       # Eliminar el entorno (¡cuidado!)
```
