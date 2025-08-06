"""
Integration tests for Neon Database operations.
These tests use REAL Neon database and MUST FAIL if the database is not accessible.
"""

import pytest
import pytest_asyncio
import os
import uuid
import asyncio
from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
import logging

from app.database.config import AsyncSessionLocal
from app.models.video_analysis import VideoAnalysis, AnalysisStatus
from app.models.user import User
from app.models.video import Video

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture(scope="module")
async def verify_database_connection():
    """Verify database is accessible before running tests"""
    try:
        async with AsyncSessionLocal() as session:
            # Test basic connectivity
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1, "Database connectivity check failed"
            
            # Verify we're connected to Neon (check for Neon-specific settings)
            result = await session.execute(text("SELECT current_setting('server_version')"))
            version = result.scalar()
            logger.info(f"Connected to PostgreSQL version: {version}")
            
    except Exception as e:
        pytest.fail(f"Neon database integration test failed - database not accessible: {e}")


@pytest_asyncio.fixture
async def db_session():
    """Provide a database session for tests"""
    async with AsyncSessionLocal() as session:
        yield session
        # Don't commit by default - let tests handle it
        await session.rollback()


@pytest_asyncio.fixture
async def test_user():
    """Create a test user for foreign key constraints - returns user ID only"""
    user_id = None
    
    # Create user in its own session
    async with AsyncSessionLocal() as session:
        user = User(
            email=f"test_{uuid.uuid4().hex}@example.com",
            hashed_password="hashed_password_123"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        user_id = user.id
    
    yield user_id
    
    # Cleanup in its own session
    if user_id:
        async with AsyncSessionLocal() as session:
            user = await session.get(User, user_id)
            if user:
                await session.delete(user)
                await session.commit()


@pytest.mark.integration
@pytest.mark.requires_neon
class TestNeonDatabaseOperations:
    """Test real Neon database operations"""
    
    @pytest.mark.asyncio
    async def test_neon_connection_real(self, verify_database_connection):
        """Test real Neon DB connection - MUST FAIL if DB is not accessible"""
        try:
            async with AsyncSessionLocal() as session:
                # Test connection
                result = await session.execute(text("SELECT 1"))
                assert result.scalar() == 1, "Basic query failed"
                
                # Test Neon-specific features (e.g., extensions)
                result = await session.execute(text("""
                    SELECT extname 
                    FROM pg_extension 
                    WHERE extname IN ('uuid-ossp', 'pg_stat_statements')
                """))
                extensions = [row[0] for row in result]
                logger.info(f"Available extensions: {extensions}")
                
        except Exception as e:
            pytest.fail(f"Neon connection test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_analysis_crud_real(self, test_user):
        """Test real CRUD operations on VideoAnalysis table"""
        async with AsyncSessionLocal() as db_session:
            try:
                # CREATE
                analysis = VideoAnalysis(
                    user_id=test_user,  # test_user is now just the ID
                    uuid=uuid.uuid4(),
                    status=AnalysisStatus.PENDING
                )
                db_session.add(analysis)
                await db_session.commit()
                await db_session.refresh(analysis)
                
                analysis_id = analysis.id
                analysis_uuid = analysis.uuid
                
                # READ
                result = await db_session.execute(
                    select(VideoAnalysis).filter(VideoAnalysis.uuid == analysis_uuid)
                )
                fetched = result.scalar_one_or_none()
                assert fetched is not None, "Failed to read created analysis"
                assert fetched.status == AnalysisStatus.PENDING
                
                # UPDATE
                fetched.status = AnalysisStatus.PROCESSING
                fetched.processing_started_at = datetime.utcnow()
                await db_session.commit()
                
                # Verify update
                result = await db_session.execute(
                    select(VideoAnalysis).filter(VideoAnalysis.id == analysis_id)
                )
                updated = result.scalar_one_or_none()
                assert updated.status == AnalysisStatus.PROCESSING
                assert updated.processing_started_at is not None
                
                # DELETE
                await db_session.delete(updated)
                await db_session.commit()
                
                # Verify deletion
                result = await db_session.execute(
                    select(VideoAnalysis).filter(VideoAnalysis.id == analysis_id)
                )
                deleted = result.scalar_one_or_none()
                assert deleted is None, "Failed to delete analysis"
                
            except Exception as e:
                pytest.fail(f"CRUD operations test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_enum_status_values(self, test_user):
        """Test that enum status values work correctly with database"""
        async with AsyncSessionLocal() as db_session:
            try:
                # Test all valid status values
                for status in AnalysisStatus:
                    analysis = VideoAnalysis(
                        user_id=test_user,  # test_user is now just the ID
                        uuid=uuid.uuid4(),
                        status=status
                    )
                    db_session.add(analysis)
                    await db_session.commit()
                    await db_session.refresh(analysis)
                    
                    # Verify status was saved correctly
                    assert analysis.status == status, f"Status {status} not saved correctly"
                    
                    # Clean up
                    await db_session.delete(analysis)
                    await db_session.commit()
                    
            except Exception as e:
                pytest.fail(f"Enum status test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_uuid_uniqueness_constraint(self, test_user):
        """Test UUID uniqueness constraint in database"""
        async with AsyncSessionLocal() as db_session:
            try:
                # Create first analysis
                test_uuid = uuid.uuid4()
                analysis1 = VideoAnalysis(
                    user_id=test_user,
                    uuid=test_uuid,
                    status=AnalysisStatus.PENDING
                )
                db_session.add(analysis1)
                await db_session.commit()
                
                # Try to create second with same UUID
                analysis2 = VideoAnalysis(
                    user_id=test_user,
                    uuid=test_uuid,  # Same UUID
                    status=AnalysisStatus.PENDING
                )
                db_session.add(analysis2)
                
                # This should raise IntegrityError
                with pytest.raises(IntegrityError) as exc_info:
                    await db_session.commit()
                
                assert "unique" in str(exc_info.value).lower() or "duplicate" in str(exc_info.value).lower()
                
                # Rollback and cleanup
                await db_session.rollback()
                await db_session.delete(analysis1)
                await db_session.commit()
                
            except IntegrityError:
                # Expected
                await db_session.rollback()
            except Exception as e:
                pytest.fail(f"UUID uniqueness test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_concurrent_database_access(self, test_user):
        """Test concurrent database operations"""
        try:
            # Create multiple concurrent tasks
            async def create_analysis(index):
                async with AsyncSessionLocal() as session:
                    analysis = VideoAnalysis(
                        user_id=test_user,
                        uuid=uuid.uuid4(),
                        status=AnalysisStatus.PENDING
                    )
                    session.add(analysis)
                    await session.commit()
                    return analysis.id
            
            # Run concurrently
            tasks = [create_analysis(i) for i in range(5)]
            analysis_ids = await asyncio.gather(*tasks)
            
            # Verify all were created
            assert len(analysis_ids) == 5, "Not all concurrent creates succeeded"
            assert len(set(analysis_ids)) == 5, "Duplicate IDs created"
            
            # Cleanup
            async with AsyncSessionLocal() as session:
                for aid in analysis_ids:
                    analysis = await session.get(VideoAnalysis, aid)
                    if analysis:
                        await session.delete(analysis)
                await session.commit()
                
        except Exception as e:
            pytest.fail(f"Concurrent access test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, test_user):
        """Test transaction rollback behavior"""
        async with AsyncSessionLocal() as db_session:
            try:
                # Start transaction
                analysis = VideoAnalysis(
                    user_id=test_user,
                    uuid=uuid.uuid4(),
                    status=AnalysisStatus.PENDING
                )
                db_session.add(analysis)
                await db_session.flush()  # Get ID without committing
                
                analysis_id = analysis.id
                assert analysis_id is not None, "ID not assigned after flush"
                
                # Rollback
                await db_session.rollback()
                
                # Verify not in database
                result = await db_session.execute(
                    select(VideoAnalysis).filter(VideoAnalysis.id == analysis_id)
                )
                fetched = result.scalar_one_or_none()
                assert fetched is None, "Rolled back record still in database"
                
            except Exception as e:
                pytest.fail(f"Transaction rollback test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_jsonb_fields(self, test_user):
        """Test JSONB field operations"""
        async with AsyncSessionLocal() as db_session:
            try:
                # Create analysis with JSONB data
                analysis_data = {
                    "swing_metrics": {
                        "speed": 95.5,
                        "angle": 45.2,
                        "quality": "excellent"
                    },
                    "timestamps": [1.0, 2.5, 3.8]
                }
                
                analysis = VideoAnalysis(
                    user_id=test_user,
                    uuid=uuid.uuid4(),
                    status=AnalysisStatus.COMPLETED,
                    analysisJSON=analysis_data,
                    ai_analysis={"legacy": "data"},
                    swing_metrics={"club_speed": 90}
                )
                db_session.add(analysis)
                await db_session.commit()
                await db_session.refresh(analysis)
                
                # Verify JSONB data
                assert analysis.analysisJSON == analysis_data
                assert analysis.analysisJSON["swing_metrics"]["speed"] == 95.5
                assert len(analysis.analysisJSON["timestamps"]) == 3
                
                # Query by JSONB field (PostgreSQL specific)
                result = await db_session.execute(
                    text("""
                        SELECT id FROM video_analyses 
                        WHERE analysis_json @> '{"swing_metrics": {"quality": "excellent"}}'
                        AND id = :id
                    """),
                    {"id": analysis.id}
                )
                found_id = result.scalar()
                assert found_id == analysis.id, "JSONB query failed"
                
                # Cleanup
                await db_session.delete(analysis)
                await db_session.commit()
                
            except Exception as e:
                pytest.fail(f"JSONB fields test failed: {e}")


@pytest.mark.integration
@pytest.mark.requires_neon
class TestNeonPerformance:
    """Test Neon database performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, test_user):
        """Test bulk insert performance"""
        try:
            start_time = datetime.utcnow()
            
            async with AsyncSessionLocal() as session:
                # Create multiple records
                analyses = []
                for i in range(100):
                    analysis = VideoAnalysis(
                        user_id=test_user,
                        uuid=uuid.uuid4(),
                        status=AnalysisStatus.PENDING
                    )
                    analyses.append(analysis)
                
                # Bulk insert
                session.add_all(analyses)
                await session.commit()
                
                # Get IDs for cleanup
                analysis_ids = [a.id for a in analyses]
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Bulk insert of 100 records took {elapsed:.2f} seconds")
            
            # Verify reasonable performance (should be < 5 seconds for 100 records)
            assert elapsed < 5.0, f"Bulk insert too slow: {elapsed} seconds"
            
            # Cleanup
            async with AsyncSessionLocal() as session:
                await session.execute(
                    text("DELETE FROM video_analyses WHERE id = ANY(:ids)"),
                    {"ids": analysis_ids}
                )
                await session.commit()
                
        except Exception as e:
            pytest.fail(f"Bulk insert performance test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_query_performance(self, test_user):
        """Test query performance with indexes"""
        try:
            # Create test data
            async with AsyncSessionLocal() as session:
                test_uuid = uuid.uuid4()
                analysis = VideoAnalysis(
                    user_id=test_user,
                    uuid=test_uuid,
                    status=AnalysisStatus.COMPLETED
                )
                session.add(analysis)
                await session.commit()
                analysis_id = analysis.id
            
            # Test indexed query (UUID has unique index)
            start_time = datetime.utcnow()
            
            async with AsyncSessionLocal() as session:
                for _ in range(100):
                    result = await session.execute(
                        select(VideoAnalysis).filter(VideoAnalysis.uuid == test_uuid)
                    )
                    _ = result.scalar_one_or_none()
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"100 indexed queries took {elapsed:.2f} seconds")
            
            # Should be fast with index (< 1 second for 100 queries)
            assert elapsed < 1.0, f"Indexed queries too slow: {elapsed} seconds"
            
            # Cleanup
            async with AsyncSessionLocal() as session:
                analysis = await session.get(VideoAnalysis, analysis_id)
                if analysis:
                    await session.delete(analysis)
                    await session.commit()
                    
        except Exception as e:
            pytest.fail(f"Query performance test failed: {e}")