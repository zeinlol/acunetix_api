from api.classes.source import AcunetixSource


class AcunetixReport:
    def __init__(self,
                 download: list[str] | None,
                 generation_date: str,
                 report_id: str,
                 template_id: str,
                 template_name: str,
                 template_type: int,
                 status: str,
                 source: dict, ):
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
        return self._download_link_name('pdf')

    @property
    def download_html(self) -> str:
        return self._download_link_name('html')

    def _download_link_name(self, link_name: str) -> str:
        return (
            [link for link in self.download if link.endswith(link_name)][-1] or ''
            if self.download
            else ''
        )

    @property
    def download_html_name(self) -> str:
        return self.download_html.split('/')[-1]

    @property
    def download_pdf_name(self) -> str:
        return self.download_pdf.split('/')[-1]

    @staticmethod
    def init_source(source: dict) -> AcunetixSource:
        return AcunetixSource(
            list_type=source['list_type'],
            description=source.get('description', ''),
            id_list=source['id_list'],
        )
