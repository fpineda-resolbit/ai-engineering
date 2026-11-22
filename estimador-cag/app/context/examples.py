"""Contexto estático (CAG): estimaciones históricas que se inyectan en el system prompt.

Funcionan como few-shot examples: marcan el formato, el nivel de detalle y las tarifas
que el modelo debe seguir al estimar un proyecto nuevo.
"""

ESTIMATION_EXAMPLES: list[dict[str, str]] = [
    {
        "meeting_summary": (
            "Una cadena de ferreterías necesita una plataforma web interna de gestión de "
            "inventario para sus 5 tiendas: alta y baja de productos, control de stock por "
            "tienda, alertas de stock mínimo, roles (administrador, encargado de tienda) y un "
            "dashboard con métricas de rotación. Ya tienen un ERP del que exportan CSV."
        ),
        "estimation": """\
## Estimación: Plataforma de Gestión de Inventario

### Desglose de tareas
| # | Tarea | Horas |
|---|-------|-------|
| 1 | Descubrimiento y diseño UI/UX | 40 |
| 2 | Backend API (CRUD productos, stock por tienda) | 60 |
| 3 | Importación de CSV desde el ERP | 16 |
| 4 | Autenticación y roles | 20 |
| 5 | Alertas de stock mínimo (email) | 12 |
| 6 | Dashboard con métricas de rotación | 30 |
| 7 | Testing y QA | 25 |
| 8 | Despliegue y documentación | 10 |

**Total estimado: 213 horas (≈ 12.780 €, tarifa media 60 €/h)**
**Equipo recomendado: 2 desarrolladores full-stack + 1 diseñador UX (part-time)**
**Duración estimada: 7-8 semanas**

### Supuestos y riesgos
- El formato del CSV del ERP es estable; una integración vía API se estimaría aparte.
- Riesgo: datos de stock históricos inconsistentes entre tiendas.
""",
    },
    {
        "meeting_summary": (
            "Una clínica de fisioterapia quiere una app móvil (iOS y Android) para que sus "
            "pacientes reserven citas, reciban recordatorios push y vean sus ejercicios en "
            "vídeo. Los fisioterapeutas gestionan agenda y ejercicios desde un panel web. "
            "Pagos online opcionales en una segunda fase."
        ),
        "estimation": """\
## Estimación: App de Reservas para Clínica de Fisioterapia

### Desglose de tareas
| # | Tarea | Horas |
|---|-------|-------|
| 1 | Diseño UI/UX (app + panel web) | 50 |
| 2 | App móvil multiplataforma (Flutter): registro, reservas, perfil | 90 |
| 3 | Notificaciones push y recordatorios | 18 |
| 4 | Biblioteca de ejercicios en vídeo (subida y streaming) | 30 |
| 5 | Backend API y gestión de agenda | 70 |
| 6 | Panel web para fisioterapeutas | 45 |
| 7 | Testing y QA (incluye dispositivos reales) | 35 |
| 8 | Publicación en App Store y Google Play | 12 |

**Total estimado: 350 horas (≈ 21.000 €, tarifa media 60 €/h)**
**Equipo recomendado: 1 desarrollador móvil + 1 backend + 1 diseñador UX (part-time)**
**Duración estimada: 10-12 semanas**

### Supuestos y riesgos
- Pagos online fuera de alcance (fase 2, estimación aparte: ~40 h).
- Riesgo: tiempos de revisión de las tiendas de apps.
- Datos de salud: requiere revisión RGPD.
""",
    },
]


def format_examples(examples: list[dict[str, str]] = ESTIMATION_EXAMPLES) -> str:
    """Formatea los ejemplos como bloque de texto para el system prompt."""
    blocks = [
        f"### Ejemplo {i}\n"
        f"**Resumen de la reunión:** {ex['meeting_summary']}\n\n"
        f"**Estimación entregada:**\n{ex['estimation']}"
        for i, ex in enumerate(examples, start=1)
    ]
    return "\n---\n\n".join(blocks)
