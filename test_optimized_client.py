"""Test script to demonstrate optimized Odoo client performance improvements"""

import asyncio
import time
from app.odoo.optimized_client import OptimizedOdooClient
from app.config import settings


async def test_optimized_client():
    """Test the optimized Odoo client with various operations"""
    
    print("=== Testing Optimized Odoo Client ===")
    
    # Create optimized client
    client = OptimizedOdooClient(
        settings.ODOO_URL,
        settings.ODOO_DB,
        settings.ODOO_USERNAME,
        settings.ODOO_PASSWORD
    )
    
    try:
        # Authenticate
        await client.authenticate()
        print("✓ Authentication successful")
        
        # Test 1: Prepare query for projects
        print("\n1. Testing prepared queries...")
        start_time = time.time()
        
        await client.prepare_query(
            query_name="project_list",
            model="project.project",
            base_fields=["id", "name", "description", "progress"]
        )
        
        # Execute prepared query multiple times
        for i in range(3):
            projects = await client.execute_prepared_query("project_list", limit=5)
            print(f"  Query {i+1}: Found {len(projects)} projects")
        
        prep_time = time.time() - start_time
        print(f"  Prepared queries completed in {prep_time:.3f}s")
        
        # Test 2: Query builder
        print("\n2. Testing query builder...")
        start_time = time.time()
        
        projects = await client.build_query(
            model="project.project",
            filters={"name": ("ilike", "%test%")},
            fields=["id", "name"],
            limit=10,
            order_by="name ASC"
        )
        
        query_time = time.time() - start_time
        print(f"  Query builder found {len(projects)} projects in {query_time:.3f}s")
        
        # Test 3: Batch operations
        print("\n3. Testing batch operations...")
        start_time = time.time()
        
        # Simulate multiple updates in batch mode
        if projects:
            project_id = projects[0]["id"]
            
            # Multiple updates in batch mode
            for i in range(3):
                await client.update_record_optimized(
                    model="project.project",
                    record_id=project_id,
                    values={"description": f"Test update {i}"},
                    batch_mode=True
                )
            
            # Execute all batch updates at once
            await client.execute_batch_updates("project.project")
            print(f"  Batch updates completed for project {project_id}")
        
        batch_time = time.time() - start_time
        print(f"  Batch operations completed in {batch_time:.3f}s")
        
        # Test 4: Performance stats
        print("\n4. Performance statistics:")
        stats = await client.get_performance_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print(f"\n✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")


async def compare_performance():
    """Compare performance between regular and optimized client"""
    
    print("\n=== Performance Comparison ===")
    
    # Test regular search
    from app.odoo.client import OdooClient
    
    regular_client = OdooClient(
        settings.ODOO_URL,
        settings.ODOO_DB,
        settings.ODOO_USERNAME,
        settings.ODOO_PASSWORD
    )
    
    optimized_client = OptimizedOdooClient(
        settings.ODOO_URL,
        settings.ODOO_DB,
        settings.ODOO_USERNAME,
        settings.ODOO_PASSWORD
    )
    
    await regular_client.authenticate()
    await optimized_client.authenticate()
    
    # Test 1: Single search
    print("\n1. Single search comparison:")
    
    start_time = time.time()
    regular_result = await regular_client.search_records("project.project", limit=10)
    regular_time = time.time() - start_time
    
    start_time = time.time()
    optimized_result = await optimized_client.search_records_optimized("project.project", limit=10)
    optimized_time = time.time() - start_time
    
    print(f"  Regular client: {regular_time:.3f}s, found {len(regular_result)} records")
    print(f"  Optimized client: {optimized_time:.3f}s, found {len(optimized_result)} records")
    print(f"  Improvement: {((regular_time - optimized_time) / regular_time * 100):.1f}%")
    
    # Test 2: Multiple searches
    print("\n2. Multiple searches comparison:")
    
    start_time = time.time()
    for i in range(5):
        await regular_client.search_records("project.project", limit=5)
    regular_time = time.time() - start_time
    
    # Prepare query first for optimized client
    await optimized_client.prepare_query("test_search", "project.project")
    
    start_time = time.time()
    for i in range(5):
        await optimized_client.execute_prepared_query("test_search", limit=5)
    optimized_time = time.time() - start_time
    
    print(f"  Regular client (5 searches): {regular_time:.3f}s")
    print(f"  Optimized client (5 searches): {optimized_time:.3f}s")
    print(f"  Improvement: {((regular_time - optimized_time) / regular_time * 100):.1f}%")


if __name__ == "__main__":
    print("Odoo Optimized Client Performance Test")
    print("=" * 50)
    
    # Run tests
    asyncio.run(test_optimized_client())
    asyncio.run(compare_performance())
    
    print("\n" + "=" * 50)
    print("Test completed!")