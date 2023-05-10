class AcunetixTarget:
    def __init__(self,
                 address: str,
                 fqdn: str,
                 domain: str,
                 general_type: str,
                 target_type: str,
                 target_id: str,
                 description: str = '',
                 criticality: int = 10):
        self.address = address
        self.fqdn = fqdn
        self.general_type = general_type
        self.target_type = target_type
        self.target_id = target_id
        self.domain = domain
        self.address = address
        self.description = description
        self.criticality = criticality

    def __str__(self) -> str:
        return f'{self.target_id} ({self.address})'
