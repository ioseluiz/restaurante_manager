# Usuarios

Administra **quién puede entrar** al sistema. Este módulo solo aparece para el rol **administrador**.

## Roles

| Rol | Qué ve |
|---|---|
| **admin** | Todo, incluida la gestión de usuarios y la configuración de la base de datos |
| **gerente** | Todo menos Usuarios y Configurar BD |
| **empleado** | Solo la operación diaria: Ventas, Compras, Inventario, Toma de Inventario, Catálogo de Insumos, Etiquetas, Recetas, Menú y Unidades. No ve el Panel de Control, Presupuestos, Consolidados, Rentabilidad, Costo de Platos, Análisis de Precios, Planilla (salarios y finanzas) ni Sucursales. Al entrar abre Ventas |

## Tareas

| Quiero… | Cómo |
|---|---|
| Crear un usuario | **Nuevo Usuario**: nombre de usuario, contraseña y rol → **Guardar Usuario** |
| Cambiar contraseña o rol | Seleccione la fila → **Editar Seleccionado** |
| Quitar un acceso | Seleccione la fila → **Eliminar Usuario** |

## Seguridad

- El usuario administrador inicial (**admin**) no permite cambiar su nombre ni su rol, para evitar quedarse sin acceso.
- **Cambie la contraseña inicial** del administrador la primera vez que ingrese.
- Las contraseñas se guardan cifradas con una sal propia por usuario; nadie puede leerlas, ni siquiera el administrador. Si alguien la olvida, asígnele una nueva con **Editar Seleccionado**.
- Cree un usuario por persona; no comparta cuentas.
- Elimine el usuario de quien deja de trabajar en el restaurante.
