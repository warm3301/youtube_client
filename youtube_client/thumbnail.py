class Thumbnail:
    def __init__(self,url:str):
        self.url:str = url
        self.width:int = None
        self.height:int = None
    def __repr__(self)->str:
        return f"<Thumbnail url=\"{self.url}\"/>"
    