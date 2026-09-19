from dataclasses import dataclass

import firebase_admin

from firebase_admin import (
    auth,
    firestore,
)

from django.conf import settings

from rest_framework.authentication import (
    BaseAuthentication,
    get_authorization_header,
)

from rest_framework.exceptions import AuthenticationFailed


@dataclass
class FirebaseUser:
    uid: str
    email: str | None = None
    is_authenticated: bool = True

    @property
    def pk(self):
        return self.uid


def _ensure_app():
    if firebase_admin._apps:
        return

    options = (
        {
            "projectId": settings.FIREBASE_PROJECT_ID,
        }
        if settings.FIREBASE_PROJECT_ID
        else None
    )

    firebase_admin.initialize_app(
        options=options,
    )


def get_firestore_client():
    _ensure_app()

    return firestore.client()


class FirebaseAuthentication(BaseAuthentication):
    keyword = b"Bearer"

    def authenticate(self, request):
        header = get_authorization_header(
            request
        ).split()

        if not header:
            return None

        if (
            len(header) != 2
            or header[0].lower() != b"bearer"
        ):
            raise AuthenticationFailed(
                "Malformed Authorization header."
            )

        try:
            _ensure_app()

            decoded = auth.verify_id_token(
                header[1].decode("utf-8"),
                check_revoked=False,
            )

        except (
            ValueError,
            auth.InvalidIdTokenError,
            auth.ExpiredIdTokenError,
            auth.RevokedIdTokenError,
            auth.CertificateFetchError,
        ):
            raise AuthenticationFailed(
                "Invalid or expired Firebase ID token."
            )

        uid = (
            decoded.get("uid")
            or decoded.get("sub")
        )

        if not uid:
            raise AuthenticationFailed(
                "Firebase token does not contain a UID."
            )

        return (
            FirebaseUser(
                uid=uid,
                email=decoded.get("email"),
            ),
            decoded,
        )

    def authenticate_header(
        self,
        request,
    ):
        return "Bearer"