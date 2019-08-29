import json, csv, os


class IANAFormats:
    def __init__(self):
        self.names = set()
        self.endings = set()
        self.mimetypes = set()

        for p in ['application.csv', 'audio.csv', 'image.csv', 'message.csv', 'model.csv', 'multipart.csv', 'text.csv',
                  'video.csv']:
            with open(os.path.join('resources/iana', p)) as f:
                reader = csv.reader(f)
                # skip header
                next(reader)
                for row in reader:
                    self.names.add(row[0].strip().lower())
                    self.mimetypes.add(row[1].strip().lower())
        with open(os.path.join('resources/iana', 'mimetypes.json')) as f:
            mappings = json.load(f)
            for dict in mappings:
                for k in dict:
                    if dict[k] in self.mimetypes:
                        self.endings.add(k[1:])

    def is_in_iana(self, v):
        return v in self.names or v in self.mimetypes or v in self.endings