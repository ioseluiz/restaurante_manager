# [FILE: app/database/costeo_sql.py]
"""SQL compartido del módulo Costo de platos (conexión, controladores y vistas)."""

# Factor tanda -> porción para SQL (alias `m` = menu_items). 1.0 si la receta es por porción.
# Porción y rendimiento comparten unidad (el editor lo fuerza).
SQL_FACTOR_PORCION = (
    "(CASE WHEN COALESCE(m.rendimiento,0) > 0 AND COALESCE(m.porcion_servida,0) > 0 "
    "THEN m.porcion_servida * 1.0 / m.rendimiento ELSE 1.0 END)"
)

# Insumos por PORCIÓN de cada ítem del menú, incluyendo los de sus sub-recetas
# (recursivo, prof. máx. 6 para cortar ciclos).
#   raíz: multiplicador = factor tanda->porción del plato
#   hijo: multiplicador = mult_padre * cantidad_usada / rendimiento_del_componente
# Las cantidades de receta_componentes ya están en la unidad de rendimiento del
# componente (el editor y el importador lo garantizan).
NOMBRE_VISTA_RECETAS = "v_recetas_explotadas"
SQL_VISTA_RECETAS_EXPLOTADAS = f"""
CREATE VIEW {NOMBRE_VISTA_RECETAS} AS
WITH RECURSIVE expl(raiz, nodo, mult, prof) AS (
    SELECT m.id, m.id, {SQL_FACTOR_PORCION}, 0 FROM menu_items m
    UNION ALL
    SELECT e.raiz, rc.componente_id,
           e.mult * rc.cantidad / COALESCE(NULLIF(c.rendimiento, 0), 1.0),
           e.prof + 1
    FROM expl e
    JOIN receta_componentes rc ON rc.menu_item_id = e.nodo
    JOIN menu_items c ON c.id = rc.componente_id
    WHERE e.prof < 6
)
SELECT e.raiz AS menu_item_id, r.insumo_id AS insumo_id,
       SUM(r.cantidad_necesaria * e.mult) AS cantidad_necesaria
FROM expl e
JOIN recetas r ON r.menu_item_id = e.nodo
GROUP BY e.raiz, r.insumo_id
"""
