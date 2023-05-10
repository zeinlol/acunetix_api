from api.classes.target import AcunetixTarget


class AcunetixScanSession:
    def __init__(self,
                 status: str,
                 threat: int = 0,
                 progress: str = None,
                 scan_session_id: str = None,
                 severity_counts: int = None,
                 start_date: str = None,
                 event_level: int = 0):
        self.status = status
        self.threat = threat
        self.progress = progress
        self.scan_session_id = scan_session_id
        self.severity_counts = severity_counts
        self.start_date = start_date
        self.event_level = event_level


class AcunetixScan:
    def __init__(self,
                 current_session: dict,
                 profile_id: str,
                 scan_id: str,
                 target_id: str,
                 target: dict,
                 report_template_id: str = '',
                 profile_name: str = '',
                 next_run: str = '',
                 max_scan_time: int = 0,
                 incremental: bool = False,
                 criticality: int = 10,):
        self.scan_id = scan_id
        self.target_id = target_id
        self.report_template_id = report_template_id
        self.profile_id = profile_id
        self.profile_name = profile_name
        self.next_run = next_run
        self.max_scan_time = max_scan_time
        self.incremental = incremental
        self.current_session = self.init_session(current_session=current_session)
        self.target = self.init_target(target=target)
        self.criticality = criticality

    @staticmethod
    def init_session(current_session: dict) -> AcunetixScanSession:
        return AcunetixScanSession(
            status=current_session['status'],
            threat=current_session.get('threat'),
            progress=current_session.get('progress'),
            scan_session_id=current_session.get('scan_session_id'),
            severity_counts=current_session.get('severity_counts'),
            start_date=current_session.get('start_date'),
            event_level=current_session.get('event_level'),
        )

    def init_target(self, target: dict) -> AcunetixTarget:
        return AcunetixTarget(
            address=target['address'],
            fqdn=target.get('fqdn'),
            domain=target.get('domain'),
            general_type=target.get('type', 'default') or 'default',  # can be None
            target_type=target.get('target_type', 'default') or 'default',  # can be None
            target_id=self.target_id,
            description=target.get('description', ''),
            criticality=target.get('criticality', 10),
        )

    def __str__(self) -> str:
        return f'Scan {self.scan_id} for target {self.target}'
