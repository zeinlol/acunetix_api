class AcunetixReportSource:
    def __init__(self,
                 list_type: str,
                 description: str,
                 id_list: list[str],):
        self.list_type = list_type
        self.description = description
        self.id_list = id_list


class AcunetixReport:
    def __init__(self,
                 download: list[str],
                 generation_date: str,
                 report_id: str,
                 template_id: str,
                 template_name: str,
                 template_type: int,
                 status: str,
                 source: dict,):
        self.download = download
        self.generation_date = generation_date
        self.report_id = report_id
        self.template_id = template_id
        self.template_name = template_name
        self.template_type = template_type
        self.status = status
        self.source = self.init_source(source=source)

    def __str__(self) -> str:
        return f'Report {self.report_id} ({self.template_name})'

    @property
    def download_pdf(self) -> str:
        return [link for link in self.download if link.endswith('pdf')][-1]

    @property
    def download_html(self) -> str:
        return [link for link in self.download if link.endswith('html')][-1]

    @property
    def download_html_name(self) -> str:
        return self.download_html.split('/')[-1]

    @property
    def download_pdf_name(self) -> str:
        return self.download_pdf.split('/')[-1]

    @staticmethod
    def init_source(source: dict) -> AcunetixReportSource:
        return AcunetixReportSource(
            list_type=source['list_type'],
            description=source['description'],
            id_list=source['id_list'],
        )
