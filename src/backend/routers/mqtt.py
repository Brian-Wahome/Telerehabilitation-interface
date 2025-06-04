from fastapi import APIRouter, HTTPException, Depends
from src.backend.service.mqtt_service import MQTTService
from src.backend.dependencies.services import get_mqtt_service
from pydantic import BaseModel

router = APIRouter(
    prefix="/mqtt",
    tags=["mqtt"]
)


class MqttClientConfig(BaseModel):
    client_id: str | None = None


@router.post("/connect", status_code=200)
def setup_client(
        mqtt_config: MqttClientConfig,
        mqtt_service: MQTTService = Depends(get_mqtt_service)
):
    try:
        if mqtt_config.client_id is not None:
            mqtt_service.setup_mqtt_client(client_id=mqtt_config.client_id)
        else:
            mqtt_service.setup_mqtt_client()
        return {"message": "Client successfully setup."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/disconnect", status_code=200)
def disconnect_client(
        mqtt_config: MqttClientConfig,
        mqtt_service: MQTTService = Depends(get_mqtt_service)
):
    try:
        if mqtt_config.client_id is not None:
            mqtt_service.disconnect_client(mqtt_config.client_id)
        else:
            mqtt_service.disconnect_client()
        return {"message": "Client successfully disconnected."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
