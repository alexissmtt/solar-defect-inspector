"""Visual quality-inspection service.

The package is split so the inspection logic does not depend on any delivery
mechanism. The core (`classifier`, `reporter`, `service`, `db`) knows nothing
about HTTP or Streamlit; the API, the batch pipeline and the frontend are thin
adapters around it.
"""

__version__ = "2.0.0"
