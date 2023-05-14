from api.classes.report import AcunetixReport


class AcunetixExportReport(AcunetixReport):

    @property
    def download_json(self) -> str:
        return self._download_link_name('json')

    @property
    def download_json_name(self) -> str:
        return self.download_json.split('/')[-1]
