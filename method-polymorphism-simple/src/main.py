class Format:
    pass

class PDF(Format):
    def export(self, data):
        print("Exporting to PDF. Data: " + str(data))

class CSV(Format):
    def export(self, data):
        print("Exporting to CSV. Data: " + str(data))

class FormatManager:
    def render(self, format, data):
        format.export(data)

if __name__ == "__main__":
    data = "This is the data"
    manager = FormatManager()
    manager.render(PDF(), data)
    manager.render(CSV(), data)