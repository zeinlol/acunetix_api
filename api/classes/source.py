class AcunetixSource:
    def __init__(self,
                 list_type: str,
                 id_list: list[str],
                 description: str = '', ):
        self.list_type = list_type
        self.description = description
        self.id_list = id_list
