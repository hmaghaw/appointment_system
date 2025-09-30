# appointment_app/services/entity_integration.py

from typing import Optional
from ..database import get_db_cursor


class EntityIntegrationManager:
    def __init__(self, provider: str = 'clover'):
        """
        Initialize the EntityIntegrationManager with a specific provider.

        Args:
            provider: The integration provider (e.g., 'clover', 'square', 'toast')
        """
        self.provider = provider

    def entity_exists(self, entity_type: str, external_id: str, business_id: int) -> bool:
        """Check if an entity with the given external ID already exists"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                           SELECT entity_id
                           FROM restaurant_integration
                           WHERE provider = %s
                             AND entity_type = %s
                             AND external_id = %s
                             AND business_id = %s
                           """, (self.provider, entity_type, external_id, business_id))
            result = cursor.fetchone()
            if result is None:
                return False
            else:
                return result['entity_id']

    def get_external_id(self, entity_type: str, entity_id: str) -> bool:
        """Check if an entity with the given external ID already exists"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                           SELECT external_id
                           FROM restaurant_integration
                           WHERE provider = %s
                             AND entity_type = %s
                             AND entity_id = %s
                           """, (self.provider, entity_type, entity_id))
            result = cursor.fetchone()
            if result is None:
                return False
            else:
                return result['external_id']

    def create_or_update_entity(
            self,
            entity_type: str,
            entity_id: int,
            external_id: str,
            business_id: int,
            name: str = None
    ) -> None:
        """
        Create or update an integration record for any entity type

        Args:
            entity_type: The type of entity (e.g., 'modifier_group', 'modifier', 'item')
            entity_id: The internal ID of the entity
            external_id: The external system's ID for this entity
            business_id: The business this entity belongs to
            name: Display name of the entity
        """
        with get_db_cursor(commit=True) as cursor:
            query = """
                    INSERT INTO restaurant_integration
                    (entity_type, entity_id, provider, external_id, business_id, name)
                    VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY \
                    UPDATE \
                        entity_id = \
                    VALUES (entity_id), business_id = \
                    VALUES (business_id), name = \
                    VALUES (name)\
                    """
            cursor.execute(query, (
                entity_type,
                entity_id,
                self.provider,
                external_id,
                business_id,
                name
            ))

    def get_entity_id(
            self,
            entity_type: str,
            external_id: str,
            business_id: int
    ) -> Optional[int]:
        """
        Get the internal ID for an entity given its external ID

        Returns:
            The entity_id if found, None otherwise
        """
        with get_db_cursor() as cursor:
            cursor.execute("""
                           SELECT entity_id
                           FROM restaurant_integration
                           WHERE external_id = %s
                             AND provider = %s
                             AND entity_type = %s
                             AND business_id = %s
                           """, (external_id, self.provider, entity_type, business_id))
            result = cursor.fetchone()
            return result['entity_id'] if result else None

    def create_entity(
            self,
            entity_type: str,
            entity_id: int,
            external_id: str,
            business_id: int,
            name: str = None
    ) -> int:
        """
        Create an integration record for any entity type.

        Returns:
            int: The ID of the created row (auto-increment primary key, if applicable)
        """
        with get_db_cursor(commit=True) as cursor:
            query = """
                    INSERT INTO restaurant_integration
                        (entity_type, entity_id, provider, external_id, business_id, name)
                    VALUES (%s, %s, %s, %s, %s, %s) \
                    """
            cursor.execute(query, (
                entity_type,
                entity_id,
                self.provider,
                external_id,
                business_id,
                name
            ))
            return cursor.lastrowid

    def update_entity(
            self,
            entity_type: str,
            entity_id: int,
            external_id: str,
            business_id: int,
            name: str = None
    ) -> bool:
        """
        Update an integration record for any entity type.

        Returns:
            bool: True if a row was updated, False otherwise
        """
        with get_db_cursor(commit=True) as cursor:
            query = """
                    UPDATE restaurant_integration
                    SET entity_id   = %s,
                        business_id = %s,
                        name        = %s,
                        provider    = %s
                    WHERE entity_type = %s
                      AND external_id = %s \
                    """
            cursor.execute(query, (
                entity_id,
                business_id,
                name,
                self.provider,
                entity_type,
                external_id
            ))
            return cursor.rowcount > 0

    def delete_entity(
            self,
            entity_type: str,
            external_id: str,
            business_id: int
    ) -> bool:
        """
        Delete an integration record for any entity type.

        Args:
            entity_type: The type of entity (e.g., 'modifier_group', 'modifier', 'item')
            external_id: The external system's ID for this entity
            business_id: The business this entity belongs to

        Returns:
            bool: True if a row was deleted, False otherwise
        """
        with get_db_cursor(commit=True) as cursor:
            query = """
                    DELETE \
                    FROM restaurant_integration
                    WHERE entity_type = %s
                      AND external_id = %s
                      AND business_id = %s \
                    """
            cursor.execute(query, (entity_type, external_id, business_id))
            return cursor.rowcount > 0

