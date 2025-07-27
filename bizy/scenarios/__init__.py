"""Business logic scenarios demonstrating cross-framework coordination."""

from .customer_service import CustomerServiceWorkflow
from .fraud_detection import FraudDetectionScenario
from .inventory_management import InventoryManagementScenario

__all__ = [
    "CustomerServiceWorkflow",
    "FraudDetectionScenario",
    "InventoryManagementScenario"
]