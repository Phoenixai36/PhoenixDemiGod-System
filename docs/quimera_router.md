# Quimera Router Documentation

## Overview

The [`quimera_router.py`](quimera_router.py) file is a FastAPI application that routes requests to different models. It uses `ContextManager` to manage the context for each zone.

## Functions

### `is_model_running(model_name)`

This function checks if a model is running in a Podman container.

### `start_model_container(model_name)`

This function starts a model in a Podman container.

### `pull_model_if_needed(model_name)`

This function pulls a model from Ollama if it is not already present.

### `request_model(request: dict)`

This function is a FastAPI endpoint that requests a model. It takes a dictionary as input, which should contain the `preferred_model` and `zone`. It returns a dictionary containing the endpoint, status, and zone context.

### `status()`

This function is a FastAPI endpoint that returns the status of all models.

### `stop_model(request: dict)`

This function is a FastAPI endpoint that stops a model. It takes a dictionary as input, which should contain the `model` to stop.