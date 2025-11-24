#!/bin/bash
# Script para actualizar la base de datos

set -e

# Activar el entorno virtual si existe
if [ -f "venv/bin/activate" ]; then
	source venv/bin/activate
fi

# Exportar variables de entorno necesarias para Flask
export FLASK_APP=app
export FLASK_ENV=production

# 1. Resetear la base de datos (solo datos, no migraciones)
python -m rosemary db:reset --yes

# 2. Poblar datos iniciales
python -m rosemary db:seed

# 3. Crear migraciones
flask db migrate --message "Auto migration"

# 4. Aplicar migraciones
flask db upgrade

echo "Base de datos actualizada correctamente"
