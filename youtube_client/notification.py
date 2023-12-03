class NotificationState:#TODO to channel
    def __init__(self,raw):
        self.raw = raw
    @property
    def id(self)->int:
        return self.raw["stateId"]
    @property
    def next_state_id(self)->int:
        return self.raw.get("stateId")
    @property
    def button_is_disabled(self)->bool:
        return self.raw["state"]["buttonRenderer"]["isDisabled"]
    @property
    def button_is_disabled(self)->bool:
        return self.raw["state"]["buttonRenderer"]["isDisabled"]
    @property
    def accessibility(self)->str:
        return self.raw["state"]["buttonRenderer"]["accessibility"]["label"]
    def __repr__(self)->str:
        return f"<NotifyState {self.id} {self.accessibility}/>"
class NotificationCommand:
    def __init__(self,raw):
        self.raw = raw
    @property
    def text(self)->str:
        val = self.raw["text"].get("simpleText")
        if not val:
            val = self.raw["text"]["runs"][0]["text"]
        return val
    @property
    def is_selected(self)->bool:
        return self.raw.get("isSelected",False)
    @property
    def icon_type(self)->str:
        return self.raw["icon"]["iconType"]
    @property
    def url_param(self)->(str,str):
        if "signalServiceEndpoint" in self.raw["serviceEndpoint"]:
            return None
        return (self.raw["serviceEndpoint"]["commandMetadata"]["webCommandMetadata"]["apiUrl"],
        self.raw["serviceEndpoint"]["modifyChannelNotificationPreferenceEndpoint"]["params"])
    def __repr__(self)->str:
        return f"<NotifyCommand {self.is_selected=} {self.text}/>"

