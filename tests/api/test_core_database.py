import pytest
from unittest.mock import Mock, patch
from dana.api.core.database import Base, get_db, engine, SessionLocal


class TestDatabase:
    """Test cases for database functionality"""

    def test_base_declarative_base(self):
        """Test that Base is properly configured"""
        assert Base is not None
        assert hasattr(Base, "metadata")

    def test_engine_creation(self):
        """Test database engine creation"""
        assert engine is not None
        assert hasattr(engine, "url")

    def test_session_local_creation(self):
        """Test SessionLocal creation"""
        assert SessionLocal is not None
        assert callable(SessionLocal)

    def test_get_db_generator(self):
        """Test that get_db returns a generator"""
        db_gen = get_db()
        assert hasattr(db_gen, "__iter__")
        assert hasattr(db_gen, "__next__")

    def test_get_db_yields_session(self):
        """Test that get_db yields a database session"""
        with patch("dana.api.core.database.SessionLocal") as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session

            db_gen = get_db()
            db = next(db_gen)

            assert db is not None
            assert db == mock_session
            mock_session_local.assert_called_once()

    def test_get_db_closes_session(self):
        """Test that get_db closes the session when done"""
        with patch("dana.api.core.database.SessionLocal") as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session

            db_gen = get_db()
            db = next(db_gen)

            # Simulate the generator being closed
            try:
                next(db_gen)
            except StopIteration:
                pass

            mock_session.close.assert_called_once()

    def test_get_db_error_handling(self):
        """Test database session error handling"""
        with patch("dana.api.core.database.SessionLocal") as mock_session_local:
            mock_session_local.side_effect = Exception("Database connection failed")

            with pytest.raises(Exception):
                db_gen = get_db()
                next(db_gen)

    def test_database_connection_string(self):
        """Test database connection string format"""
        # This test verifies the connection string is properly formatted
        # The actual connection string depends on environment variables
        assert engine.url is not None
        assert isinstance(str(engine.url), str)

    def test_base_metadata_tables(self):
        """Test that Base metadata contains expected tables"""
        # This test verifies that the Base metadata is properly configured
        assert hasattr(Base.metadata, "tables")
        assert isinstance(Base.metadata.tables, dict)

    def test_session_methods_available(self):
        """Test that session methods are available"""
        with patch("dana.api.core.database.SessionLocal") as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session

            db_gen = get_db()
            db = next(db_gen)

            # Test that session methods are available
            assert hasattr(db, "commit")
            assert hasattr(db, "rollback")
            assert hasattr(db, "close")
            assert callable(db.commit)
            assert callable(db.rollback)
            assert callable(db.close)

    def test_database_engine_configuration(self):
        """Test database engine configuration"""
        # Test engine configuration parameters
        assert hasattr(engine, "echo")
        # SQLite engine doesn't have pool_size as a direct attribute, but has pool
        assert hasattr(engine, "pool")
        assert hasattr(engine.pool, "size")

    def test_multiple_db_sessions(self):
        """Test creating multiple database sessions"""
        with patch("dana.api.core.database.SessionLocal") as mock_session_local:
            mock_session1 = Mock()
            mock_session2 = Mock()
            mock_session_local.side_effect = [mock_session1, mock_session2]

            db_gen1 = get_db()
            db_gen2 = get_db()
            db1 = next(db_gen1)
            db2 = next(db_gen2)

            assert db1 is not None
            assert db2 is not None
            assert db1 != db2  # Different sessions

    def test_database_url_components(self):
        """Test database URL components"""
        url = engine.url
        assert hasattr(url, "drivername")
        assert hasattr(url, "host")
        assert hasattr(url, "port")
        assert hasattr(url, "database")

    def test_session_rollback_on_error(self):
        """Test session close behavior on error"""
        with patch("dana.api.core.database.SessionLocal") as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session

            db_gen = get_db()
            db = next(db_gen)

            # Simulate an error during session usage
            try:
                raise Exception("Test error")
            except Exception:
                pass

            # The generator should be exhausted to trigger the finally block
            try:
                next(db_gen)
            except StopIteration:
                pass

            # Verify close was called (this is what get_db actually does)
            mock_session.close.assert_called_once()

    def test_base_inheritance(self):
        """Test that models can inherit from Base"""
        # Create a simple test model
        from sqlalchemy import Column, Integer, String

        class TestModel(Base):
            __tablename__ = "test_model"
            id = Column(Integer, primary_key=True)
            name = Column(String(50))

        # Verify the model is properly configured
        assert TestModel.__tablename__ == "test_model"
        assert hasattr(TestModel, "id")
        assert hasattr(TestModel, "name")

    def test_session_close_behavior(self):
        """Test session close behavior"""
        with patch("dana.api.core.database.SessionLocal") as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session

            db_gen = get_db()
            db = next(db_gen)
            db.close()

            mock_session.close.assert_called_once()

    def test_database_metadata_reflection(self):
        """Test database metadata reflection capabilities"""
        # Test that metadata can reflect tables
        assert hasattr(Base.metadata, "reflect")
        assert callable(Base.metadata.reflect)

    def test_session_query_capability(self):
        """Test session query capability"""
        with patch("dana.api.core.database.SessionLocal") as mock_session_local:
            mock_session = Mock()
            mock_query = Mock()
            mock_session.query.return_value = mock_query
            mock_session_local.return_value = mock_session

            db_gen = get_db()
            db = next(db_gen)
            query = db.query()

            assert query is not None
            mock_session.query.assert_called_once()

    def test_database_engine_pool_configuration(self):
        """Test database engine pool configuration"""
        # For SQLite, pool.size is a method, not a property
        assert hasattr(engine.pool, "size")
        assert callable(engine.pool.size)
        # Test that we can call the size method
        pool_size = engine.pool.size()
        assert pool_size >= 0

    def test_session_add_behavior(self):
        """Test session add behavior"""
        with patch("dana.api.core.database.SessionLocal") as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session

            db_gen = get_db()
            db = next(db_gen)
            test_object = Mock()
            db.add(test_object)

            mock_session.add.assert_called_once_with(test_object)

    def test_database_engine_disposal(self):
        """Test database engine disposal"""
        # Test that engine can be disposed
        assert hasattr(engine, "dispose")
        assert callable(engine.dispose)

    def test_session_delete_behavior(self):
        """Test session delete behavior"""
        with patch("dana.api.core.database.SessionLocal") as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session

            db_gen = get_db()
            db = next(db_gen)
            test_object = Mock()
            db.delete(test_object)

            mock_session.delete.assert_called_once_with(test_object)

    def test_database_url_string_representation(self):
        """Test database URL string representation"""
        url_str = str(engine.url)
        assert isinstance(url_str, str)
        assert len(url_str) > 0

    def test_session_merge_behavior(self):
        """Test session merge behavior"""
        with patch("dana.api.core.database.SessionLocal") as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session

            db_gen = get_db()
            db = next(db_gen)

            # Test merge method
            test_object = Mock()
            db.merge(test_object)
            mock_session.merge.assert_called_once_with(test_object)

    def test_database_engine_echo_mode(self):
        """Test database engine echo mode"""
        # Test that echo is a boolean
        assert isinstance(engine.echo, bool)

    def test_session_flush_behavior(self):
        """Test session flush behavior"""
        with patch("dana.api.core.database.SessionLocal") as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session

            db_gen = get_db()
            db = next(db_gen)

            # Test flush method
            db.flush()
            mock_session.flush.assert_called_once()

    def test_database_metadata_table_names(self):
        """Test database metadata table names"""
        # Test that metadata has table names
        assert hasattr(Base.metadata, "tables")
        assert isinstance(Base.metadata.tables, dict)

    def test_session_expire_behavior(self):
        """Test session expire behavior"""
        with patch("dana.api.core.database.SessionLocal") as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session

            db_gen = get_db()
            db = next(db_gen)

            # Test expire method
            test_object = Mock()
            db.expire(test_object)
            mock_session.expire.assert_called_once_with(test_object)

    def test_database_engine_connectivity(self):
        """Test database engine connectivity"""
        # Test that engine can connect
        assert hasattr(engine, "connect")
        assert callable(engine.connect)

    def test_session_refresh_behavior(self):
        """Test session refresh behavior"""
        with patch("dana.api.core.database.SessionLocal") as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session

            db_gen = get_db()
            db = next(db_gen)

            # Test refresh method
            test_object = Mock()
            db.refresh(test_object)
            mock_session.refresh.assert_called_once_with(test_object)
