class PropVisionError(Exception):
    def __init__(self, message=None):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return str(self.message)

    def to_dict(self) -> dict:
        return {
            "type": self.__class__.__name__,
            "message": self.message
        }

class ImageLoadError(PropVisionError):
    def __init__(self, message="Failed to load image"):
        super().__init__(message)

class ImageEnhancementError(PropVisionError):
    def __init__(self, message="Image enhancement failed"):
        super().__init__(message)

class ImageQualityError(PropVisionError):
    def __init__(self, message="Image below quality threshold"):
        super().__init__(message)

class UnsupportedFormatError(PropVisionError):
    def __init__(self, message="Unsupported file format"):
        super().__init__(message)

class ModelLoadError(PropVisionError):
    def __init__(self, message="Failed to load model"):
        super().__init__(message)

class ModelInferenceError(PropVisionError):
    def __init__(self, message="Model inference failed"):
        super().__init__(message)

class ModelNotFoundError(PropVisionError):
    def __init__(self, message="Model checkpoint not found"):
        super().__init__(message)

class PipelineError(PropVisionError):
    def __init__(self, message="Pipeline execution failed"):
        super().__init__(message)

class StageError(PropVisionError):
    def __init__(self, message="Pipeline stage error", stage_name=None):
        super().__init__(message)
        self.stage_name = stage_name

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["stage_name"] = self.stage_name
        return data

class QdrantConnectionError(PropVisionError):
    def __init__(self, message="Cannot connect to Qdrant"):
        super().__init__(message)

class EmbeddingError(PropVisionError):
    def __init__(self, message="Embedding generation failed"):
        super().__init__(message)

class SearchQueryError(PropVisionError):
    def __init__(self, message="Invalid search query"):
        super().__init__(message)

class UploadError(PropVisionError):
    def __init__(self, message="File upload failed"):
        super().__init__(message)

class ListingNotFoundError(PropVisionError):
    def __init__(self, message="Listing not found"):
        super().__init__(message)

class RateLimitError(PropVisionError):
    def __init__(self, message="API rate limit exceeded"):
        super().__init__(message)
