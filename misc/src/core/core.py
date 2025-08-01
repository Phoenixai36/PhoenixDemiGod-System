import os
import sys
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from xamba_model_router import XambaModelRouter  # noqa: E402

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Core:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Core, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        try:
            self.router = XambaModelRouter()
            logger.info("Core module initialized with XambaModelRouter.")
        except NameError:
            logger.warning("XambaModelRouter is not available. Core initialization may be incomplete.")
            self.router = None
        self._initialized = True

    def route_task(self, task_type: str, task_details: dict) -> str:
        """
        Routes a task to the appropriate model using XambaModelRouter.

        Args:
            task_type: The type of the task (e.g., "text_generation", "code_generation").
            task_details: A dictionary containing details of the task.

        Returns:
            The name of the model selected for the task.
        """
        if self.router is None:
            logger.error("Cannot route task because XambaModelRouter is not available.")
            raise RuntimeError("XambaModelRouter is not available.")
        
        task = {"type": task_type, **task_details}
        logger.debug(f"Routing task: {task}")
        
        try:
            model_name = self.router.route_task(task)
            logger.info(f"Task of type '{task_type}' routed to model: '{model_name}'.")
            return model_name
        except Exception as e:
            logger.error(f"Error routing task: {e}", exc_info=True)
            raise


def main():
    """Función principal del módulo core."""
    print("Core module initialized")
    core = Core()
    try:
        model_name = core.route_task("inference", {"prompt": "hello"})
        print(f"Routed to model: {model_name}")
    except RuntimeError as e:
        print(e)


if __name__ == "__main__":
    main()