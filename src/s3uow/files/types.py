from .media import VideoContent, PdfContent, ImageContent, AudioContent, BinaryContent, TextContent, JsonContent, \
    UrlContent

type VideoOrAudio = VideoContent | AudioContent
type Media = JsonContent | VideoContent | PdfContent | ImageContent | AudioContent | TextContent | BinaryContent | UrlContent
type NotTxtFile = VideoContent | PdfContent | ImageContent | AudioContent | BinaryContent | UrlContent
