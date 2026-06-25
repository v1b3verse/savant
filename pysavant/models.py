"""Dataclass models for Savant protocol messages.

All models use snake_case attributes in Python but serialize to camelCase
for the msgpack wire format via to_dict()/from_dict().
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


def _to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _to_snake(name: str) -> str:
    result: list[str] = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0:
            result.append("_")
        result.append(ch.lower())
    return "".join(result)


@dataclass
class DeviceInfo:
    uid: str = ""
    os_type: str = "Linux"
    app: str = "pysavant"
    version: str = "0.1.0"
    model: str = "Python Client"
    make: str = "Custom"
    device_type: str = "Android"
    name: str = "pysavant"
    device_class: str = "phone"

    def to_dict(self) -> dict[str, Any]:
        return {
            "UID": self.uid,
            "OS": self.os_type,
            "app": self.app,
            "versionName": self.version,
            "model": self.model,
            "make": self.make,
            "type": self.device_type,
            "name": self.name,
            "class": self.device_class,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceInfo:
        return cls(
            uid=data.get("UID", ""),
            os_type=data.get("OS", "Linux"),
            app=data.get("app", ""),
            version=data.get("versionName", ""),
            model=data.get("model", ""),
            make=data.get("make", ""),
            device_type=data.get("type", ""),
            name=data.get("name", ""),
            device_class=data.get("class", ""),
        )


@dataclass
class DevicePresent:
    device: DeviceInfo = field(default_factory=DeviceInfo)
    message_format: int = 1
    protocol_version: str = "2.0"
    configuration_id: str = ""
    cloud_token: str = ""
    host_uid: str = ""
    home_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "device": self.device.to_dict(),
            "messageFormat": self.message_format,
            "protocolVersion": self.protocol_version,
            "configurationID": self.configuration_id,
            "cloudToken": self.cloud_token,
            "hostUID": self.host_uid,
            "homeId": self.home_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DevicePresent:
        return cls(
            device=DeviceInfo.from_dict(data.get("device", {})),
            message_format=data.get("messageFormat", 1),
            protocol_version=data.get("protocolVersion", "2.0"),
            configuration_id=data.get("configurationID", ""),
            cloud_token=data.get("cloudToken", ""),
            host_uid=data.get("hostUID", ""),
            home_id=data.get("homeId", ""),
        )


@dataclass
class DeviceResponse:
    authorized: bool = False
    authentication: bool = False
    protocol_version: int = 0
    build_number: int = 0
    configuration_status: int = 0
    host_uid: str = ""
    home_id: str = ""
    host_name: str = ""
    host_secret: str = ""
    host_time: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "authorized": self.authorized,
            "authentication": self.authentication,
            "protocolVersion": self.protocol_version,
            "buildNumber": self.build_number,
            "configurationStatus": self.configuration_status,
            "hostUID": self.host_uid,
            "homeID": self.home_id,
            "hostName": self.host_name,
            "hostSecret": self.host_secret,
            "hostTime": self.host_time,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceResponse:
        return cls(
            authorized=data.get("authorized", False),
            authentication=data.get("authentication", False),
            protocol_version=data.get("protocolVersion", 0),
            build_number=data.get("buildNumber", 0),
            configuration_status=data.get("configurationStatus", 0),
            host_uid=data.get("hostUID", ""),
            home_id=data.get("homeID", ""),
            host_name=data.get("hostName", ""),
            host_secret=data.get("hostSecret", ""),
            host_time=data.get("hostTime", 0),
        )


@dataclass
class AuthRequest:
    user: str = ""
    password: str = ""
    pin_code: str = ""
    host_token: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict, omitting empty fields."""
        d: dict[str, Any] = {}
        if self.user:
            d["user"] = self.user
        if self.password:
            d["password"] = self.password
        if self.pin_code:
            d["pinCode"] = self.pin_code
        if self.host_token:
            d["hostToken"] = self.host_token
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuthRequest:
        return cls(
            user=data.get("user", ""),
            password=data.get("password", ""),
            pin_code=data.get("pinCode", ""),
            host_token=data.get("hostToken", ""),
        )


@dataclass
class AuthResponse:
    authorized: bool = False
    host_token: str = ""
    secret_key: str = ""
    error_code: int = 0
    error_reason: str = ""
    permissions: dict[str, Any] = field(default_factory=dict)
    configuration_uid: str = ""
    start_zone: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "authorized": self.authorized,
            "hostToken": self.host_token,
            "secretKey": self.secret_key,
            "errorCode": self.error_code,
            "errorReason": self.error_reason,
            "permissions": self.permissions,
            "configurationUID": self.configuration_uid,
            "startZone": self.start_zone,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuthResponse:
        return cls(
            authorized=data.get("authorized", False),
            host_token=data.get("hostToken", ""),
            secret_key=data.get("secretKey", ""),
            error_code=data.get("errorCode", 0),
            error_reason=data.get("errorReason", ""),
            permissions=data.get("permissions", {}),
            configuration_uid=data.get("configurationUID", ""),
            start_zone=data.get("startZone", ""),
        )


@dataclass
class MessageWrapper:
    uri: str = ""
    messages: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "URI": self.uri,
            "messages": self.messages,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MessageWrapper:
        return cls(
            uri=data.get("URI", ""),
            messages=data.get("messages", []),
        )


@dataclass
class StateRegister:
    state: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"state": self.state}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateRegister:
        return cls(state=data.get("state", ""))


@dataclass
class StateUpdate:
    state: str = ""
    value: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {"state": self.state, "value": self.value}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateUpdate:
        return cls(state=data.get("state", ""), value=data.get("value"))


@dataclass
class ServiceRequest:
    service_type: str = ""
    request: str = ""
    request_args: dict[str, Any] = field(default_factory=dict)
    zone: str = ""
    component: str = ""
    logical_component: str = ""
    variant_id: str = ""
    alias: str = ""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "serviceType": self.service_type,
            "request": self.request,
            "requestId": self.request_id,
            "zone": self.zone,
        }
        if self.request_args:
            d["requestArgs"] = self.request_args
        if self.component:
            d["component"] = self.component
        if self.logical_component:
            d["logicalComponent"] = self.logical_component
        if self.variant_id:
            d["variantID"] = self.variant_id
        if self.alias:
            d["alias"] = self.alias
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ServiceRequest:
        return cls(
            service_type=data.get("serviceType", ""),
            request=data.get("request", ""),
            request_args=data.get("requestArgs", {}),
            zone=data.get("zone", ""),
            component=data.get("component", ""),
            logical_component=data.get("logicalComponent", ""),
            variant_id=data.get("variantID", ""),
            alias=data.get("alias", ""),
            request_id=data.get("requestId", str(uuid.uuid4())),
        )


@dataclass
class ServiceResult:
    request_id: str = ""
    results: dict[str, Any] = field(default_factory=dict)
    error_code: int = 0
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "requestId": self.request_id,
            "results": self.results,
            "errorCode": self.error_code,
            "errorMessage": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ServiceResult:
        return cls(
            request_id=data.get("requestId", ""),
            results=data.get("results", {}),
            error_code=data.get("errorCode", 0),
            error_message=data.get("errorMessage", ""),
        )


@dataclass
class DISRequest:
    app: str = ""
    request: str = ""
    request_args: dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "app": self.app,
            "request": self.request,
            "requestId": self.request_id,
        }
        if self.request_args:
            d["requestArgs"] = self.request_args
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DISRequest:
        return cls(
            app=data.get("app", ""),
            request=data.get("request", ""),
            request_args=data.get("requestArgs", {}),
            request_id=data.get("requestId", str(uuid.uuid4())),
        )
