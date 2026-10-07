"""Lazy provider construction; missing optional dependencies never affect simulation."""

import logging
from functools import lru_cache
from app.core.config import settings
from app.services.hardware.base import HardwareError

log = logging.getLogger(__name__)


@lru_cache(maxsize=2)
def get_provider(name):
    if not settings.hardware_execution_enabled:
        raise HardwareError("Hardware execution is disabled")
    try:
        if name == "ibm":
            if not settings.ibm_quantum_token or not settings.ibm_quantum_instance:
                raise HardwareError("IBM Quantum credentials not configured")
            from app.services.hardware.ibm import IBMQuantumProvider

            return IBMQuantumProvider(settings)
        if name == "braket":
            if not settings.braket_region or not settings.braket_s3_bucket:
                raise HardwareError(
                    "Amazon Braket region and result bucket not configured"
                )
            from app.services.hardware.braket import AmazonBraketProvider

            return AmazonBraketProvider(settings)
        raise HardwareError("Unknown hardware provider")
    except HardwareError:
        raise
    except ImportError:
        raise HardwareError(
            "Optional provider SDK is not installed or incompatible"
        ) from None
    except Exception as exc:
        log.warning(
            "hardware_provider_initialization provider=%s error_type=%s",
            name,
            type(exc).__name__,
        )
        raise HardwareError(
            "Provider authentication or initialization failed"
        ) from None
