#!/bin/bash
# scripts/update_ai_router.sh
# Actualiza el router de IA en hpd-cli-core con la nueva versión robusta

set -e  # Salir ante cualquier error

echo "🚀 Actualizando HPD AI Router a versión robusta..."

# 1. Respaldo del router actual (si existe)
if [ -f "hpd_cli/ai_router.py" ]; then
    echo "📦 Creando respaldo de ai_router.py actual..."
    cp hpd_cli/ai_router.py hpd_cli/ai_router.py.bak
fi

# 2. Descargar o copiar la nueva versión
# (Asumimos que el archivo nuevo está en el directorio actual o en /tmp)
# Si estamos en el repositorio, podemos usar un archivo local.
# Para este ejemplo, suponemos que el nuevo código está en ./ai_router_new.py

if [ -f "./ai_router_new.py" ]; then
    echo "📄 Usando ai_router_new.py local..."
    cp ./ai_router_new.py hpd_cli/ai_router.py
else
    echo "❌ No se encontró ai_router_new.py. Descargando desde repositorio..."
    # Descargar desde una URL pública (ej: raw de GitHub)
    # URL de ejemplo (cambiar por la real)
    curl -sSL https://raw.githubusercontent.com/hpd/hpd-cli-core/main/hpd_cli/ai_router.py -o hpd_cli/ai_router.py
fi

# 3. Instalar dependencias faltantes
echo "📦 Instalando dependencias necesarias..."
pip install --upgrade tenacity google-genai python-dotenv requests rich 2>/dev/null || echo "⚠️ Algunas dependencias ya están instaladas."

# 4. Verificar que el archivo se copió correctamente
if [ -f "hpd_cli/ai_router.py" ]; then
    echo "✅ ai_router.py actualizado correctamente."
else
    echo "❌ Falló la copia de ai_router.py."
    exit 1
fi

# 5. Ejecutar pruebas de diagnóstico
echo "🧪 Ejecutando diagnóstico del nuevo router..."
python -c "
import sys
sys.path.insert(0, '.')
from hpd_cli.ai_router import get_ai_router

print('🔍 Inicializando AIRouter...')
router = get_ai_router()
print('✅ AIRouter inicializado.')

print('📊 Estado de proveedores:')
status = router.get_status()
for name, state in status.items():
    print(f'  - {name}: {state}')

print('🧪 Probando generación simple (sin contexto)...')
try:
    response = router.generate_content('Responde con un saludo corto.', task_type='fast_lookup')
    print(f'✅ Respuesta: {response[:100]}...')
except Exception as e:
    print(f'❌ Error en prueba: {e}')
    sys.exit(1)

print('🎉 Todas las pruebas pasaron.')
"

echo "✅ Actualización completada. El nuevo router está listo para usar."
