import os
from typing import Any, Dict, List, Optional

from influxdb_client.client.influxdb_client import InfluxDBClient
from influxdb_client.client.write.point import Point

from event_routing.event_store import Event, EventStoreBase


class InfluxDBEventStore(EventStoreBase):
    def __init__(self):
        self.token = os.environ.get("DOCKER_INFLUXDB_INIT_ADMIN_TOKEN")
        self.org = os.environ.get("DOCKER_INFLUXDB_INIT_ORG")
        self.bucket = os.environ.get("DOCKER_INFLUXDB_INIT_BUCKET")
        self.url = "http://localhost:8086"
        self.client = InfluxDBClient(
            url=self.url,
            token=self.token or "",
            org=self.org or ""
        )

    def store(self, event: Event) -> None:
        with self.client:
            write_api = self.client.write_api(write_options="ns")
            point = Point("event")
            point = point.tag("type", event.type)
            point = point.tag("source", event.source)
            point = point.field("payload", str(event.data))
            write_api.write(bucket=self.bucket, org=self.org, record=point)

    def get_event_by_id(self, event_id: str) -> Optional[Event]:
        with self.client:
            query_api = self.client.query_api()
            query = f"""from(bucket: "{self.bucket}")
            |> range(start: -10m)
            |> filter(fn: (r) => r._measurement == "event"
            and r.event_id == "{event_id}")"""
            query_api.query(org=self.org, query=query)
            # TODO: Procesar el resultado para reconstruir el evento
            return None  # Implementar la lógica de reconstrucción

    def query_events(self, filter_criteria: Dict[str, Any]) -> List[Event]:
        with self.client:
            query_api = self.client.query_api()
            query = f"""from(bucket: "{self.bucket}")
            |> range(start: -10m)
            |> filter(fn: (r) => r._measurement == "event" """

            # Filtrar por rango de tiempo
            if "start_time" in filter_criteria and "end_time" in filter_criteria:
                start_time = filter_criteria["start_time"]
                end_time = filter_criteria["end_time"]
                query += f""" and r._time >= "{start_time}"
                and r._time <= "{end_time}" """

            # Filtrar por otros criterios
            for key, value in filter_criteria.items():
                if key not in ["start_time", "end_time"]:
                    query += f""" and r["{key}"] == "{value}" """

            query += ")"
            query_api.query(org=self.org, query=query)
            # TODO: Procesar el resultado para reconstruir los eventos
            return []  # Implementar la lógica de reconstrucción