import enum


class AcunetixScanStatuses(enum.Enum):
    COMPLETED = 'completed'
    FAILED = 'failed'
    SCHEDULED = 'scheduled'
    PROCESSING = 'processing'


FINAL_ACUNETIX_STATUSES = [
    AcunetixScanStatuses.COMPLETED.value,
    AcunetixScanStatuses.FAILED.value,
]