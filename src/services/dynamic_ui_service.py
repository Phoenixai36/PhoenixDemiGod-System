#!/usr/bin/env python3
"""
Phoenix Hydra Dynamic UI Service
FastAPI router for serving dynamic frontend configurations.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI router
router = APIRouter()

# --- Mock Data ---

MOCK_APP_CONFIG = {
  "navigation": [
    {
      "id": "dashboard",
      "label": "Dashboard",
      "path": "/page/dashboard",
      "icon": "home"
    },
    {
      "id": "users",
      "label": "Usuarios",
      "path": "/page/users",
      "icon": "users"
    }
  ],
  "userPermissions": ["read:users", "write:users", "read:dashboard"]
}

MOCK_USERS_PAGE_LAYOUT = {
  "type": "grid",
  "layoutConfig": {
    "columns": 2,
    "gap": 16
  },
  "widgets": [
    {
      "id": "users-table",
      "component": "DataTable",
      "config": {
        "api": {
          "url": "/api/data/users",
          "method": "GET"
        },
        "columns": [
          { "key": "name", "header": "Nombre", "dataType": "string", "sortable": True },
          { "key": "email", "header": "Email", "dataType": "string" },
          { "key": "role", "header": "Rol", "dataType": "string", "filterable": True }
        ],
        "pagination": {
          "defaultPageSize": 10,
          "pageSizeOptions": [5, 10, 20]
        }
      }
    },
    {
      "id": "add-user-form",
      "component": "FormGenerator",
      "config": {
        "fields": [
          {
            "name": "name",
            "label": "Nombre de Usuario",
            "type": "text",
            "validation": [{ "type": "required", "message": "El nombre es obligatorio." }]
          },
          {
            "name": "email",
            "label": "Email",
            "type": "text",
            "validation": [{ "type": "required", "message": "El email es obligatorio." }]
          }
        ],
        "submitUrl": "/api/data/users",
        "submitMethod": "POST"
      }
    }
  ]
}

MOCK_DASHBOARD_PAGE_LAYOUT = {
    "type": "flex",
    "layoutConfig": {
        "direction": "column",
        "gap": 16
    },
    "widgets": [
        {
            "id": "welcome-banner",
            "component": "Markdown",
            "config": {
                "content": "# Welcome to the Dashboard!"
            }
        }
    ]
}

MOCK_USERS_DATA = [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "Admin"},
    {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "User"},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com", "role": "User"}
]

MOCK_LAYOUTS = {
    "users": MOCK_USERS_PAGE_LAYOUT,
    "dashboard": MOCK_DASHBOARD_PAGE_LAYOUT
}


# --- API Endpoints ---

@router.get("/config", tags=["Dynamic UI"])
async def get_app_config():
    """
    Provides the main application configuration, including navigation
    and user permissions.
    """
    return MOCK_APP_CONFIG

@router.get("/layouts/{page_name}", tags=["Dynamic UI"])
async def get_page_layout(page_name: str):
    """
    Provides the layout configuration for a specific page.
    """
    layout = MOCK_LAYOUTS.get(page_name)
    if not layout:
        raise HTTPException(
            status_code=404, detail=f"Page '{page_name}' not found."
        )
    return layout


@router.get("/data/users", tags=["Dynamic UI Data"])
async def get_users_data():
    """
    Provides data for the users table widget.
    """
    return MOCK_USERS_DATA


@router.post("/data/users", tags=["Dynamic UI Data"])
async def create_user(user_data: Dict[str, Any]):
    """
    Simulates creating a new user.
    """
    logger.info(f"Received new user data: {user_data}")
    new_user = {
        "id": len(MOCK_USERS_DATA) + 1,
        **user_data
    }
    MOCK_USERS_DATA.append(new_user)
    return new_user