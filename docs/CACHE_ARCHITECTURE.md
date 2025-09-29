# WHURL Domain Cache Architecture

## Overview

The WHURL domain cache provides an in-memory caching layer for canonical site and measurement lists. This cache enables fast existence checks, index queries, and reduces redundant HTTP requests to Hilltop servers.

## Architecture

### Components

#### DomainCache Class
The core caching component that stores normalized indexes of sites and measurements.

**Key Features:**
- **Normalized Indexing**: Site and measurement names are normalized for consistent lookups
- **HTTP Cache Validation**: Supports ETag and Last-Modified headers for efficient revalidation
- **TTL-based Expiration**: Configurable time-to-live for cached entries
- **Name Normalization**: Case-insensitive, whitespace-normalized, optional ASCII folding

#### CacheEntry Dataclass
Represents individual cache entries with metadata:

```python
@dataclass
class CacheEntry:
    data: Any                           # The cached response data
    timestamp: datetime                 # When the entry was cached
    etag: Optional[str] = None         # HTTP ETag for revalidation
    last_modified: Optional[str] = None # HTTP Last-Modified header
    expires: Optional[datetime] = None  # When the entry expires
```

### Cache Structure

#### Sites Cache
- **Primary Index**: `normalized_name -> site_data`
- **Name Mapping**: `original_name -> normalized_name`
- **Metadata**: Cache entry with ETag/Last-Modified for HTTP revalidation

#### Measurements Cache
- **Primary Index**: `(normalized_site_name, normalized_measurement_name) -> measurement_data`
- **Site Index**: `normalized_site_name -> [measurement_data, ...]`
- **Name Mapping**: `"site::measurement" -> "normalized_site::normalized_measurement"`
- **Metadata**: Cache entry with ETag/Last-Modified for HTTP revalidation

### Name Normalization

The `normalize_name()` function provides consistent name indexing:

```python
def normalize_name(name: str, ascii_fold: bool = False) -> str:
    # 1. Strip whitespace and convert to lowercase
    # 2. Collapse multiple whitespace into single spaces
    # 3. Optional ASCII folding (Café -> cafe)
```

**Examples:**
- `"Site Name"` → `"site name"`
- `"  UPPER  CASE  "` → `"upper case"`
- `"Site\t\nName"` → `"site name"`
- `"Café"` → `"café"` (or `"cafe"` with ASCII folding)

## Client Integration

### HilltopClient Cache Methods

#### Site Methods
```python
# Return cached or refreshed site list
sites = client.list_all_sites(refresh=False)

# Check if site exists (fast lookup)
exists = client.check_for_site(name, refresh=False)

# Get site metadata by name
site = client.get_site(name)

# Explicit cache refresh
client.refresh_sites()
```

#### Measurement Methods
```python
# Return cached or refreshed measurement list
measurements = client.list_all_measurements(refresh=False)

# Explicit cache refresh
client.refresh_measurements()
```

### AsyncHilltopClient
All methods have async equivalents with `await` syntax:

```python
async with AsyncHilltopClient() as client:
    sites = await client.list_all_sites()
    exists = await client.check_for_site("Site Name")
    measurements = await client.list_all_measurements()
```

## HTTP Cache Validation

### Conditional Requests
The cache implements HTTP conditional requests for efficient revalidation:

1. **First Request**: Normal HTTP request, cache response with ETag/Last-Modified
2. **Subsequent Requests**: Send `If-None-Match` (ETag) and `If-Modified-Since` headers
3. **304 Not Modified**: Server indicates cache is still valid, skip parsing
4. **200 OK**: New data received, update cache

### Cache Headers
- **ETag**: `If-None-Match` for entity tag validation
- **Last-Modified**: `If-Modified-Since` for timestamp validation

## TTL and Expiration

### Default TTL
- **Default**: 1 hour (`timedelta(hours=1)`)
- **Configurable**: Set via `DomainCache(default_ttl=custom_ttl)`

### Expiration Logic
1. Cache entries have optional `expires` timestamp
2. `cache_valid` properties check expiration status
3. Expired entries trigger automatic refresh on next access

### Manual Invalidation
```python
cache.invalidate_sites()        # Clear sites cache
cache.invalidate_measurements() # Clear measurements cache
cache.invalidate_all()         # Clear all caches
```

## Performance Characteristics

### Fast Operations (O(1) average)
- `check_for_site(name)`: Normalized name lookup
- `get_site(name)`: Direct hash table access
- Cache validity checks

### Slower Operations
- Initial cache population (HTTP request + XML parsing)
- Cache refresh (HTTP request + XML parsing)
- `list_all_*()` methods (return full lists)

## Configuration Options

### DomainCache Constructor
```python
DomainCache(
    default_ttl=timedelta(hours=1),  # Cache expiration time
    ascii_fold=False                 # Unicode to ASCII normalization
)
```

### ASCII Folding
When enabled, normalizes Unicode characters to ASCII equivalents:
- `"Café"` → `"cafe"`
- `"Naïve"` → `"naive"`

Useful for systems with inconsistent Unicode handling.

## Error Handling

### Cache Miss Behavior
- `get_site()`: Returns `None` for missing sites
- `check_for_site()`: Returns `False` for missing sites
- `get_measurements_for_site()`: Returns empty list for missing sites

### HTTP Error Handling
- HTTP errors bubble up through existing client error handling
- 304 Not Modified responses handled gracefully (cache remains valid)
- Network failures don't affect existing cached data

## Thread Safety

**Current Implementation**: Not thread-safe
- Cache operations are not atomic
- Concurrent access may cause race conditions

**Future Enhancement**: Thread-safe implementation using locks or concurrent data structures

## Memory Usage

### Estimation
- **Sites**: ~100-1000 entries × ~1KB each = 100KB-1MB
- **Measurements**: ~1000-10000 entries × ~500B each = 500KB-5MB
- **Total**: Typically under 10MB for reasonable Hilltop server datasets

### Memory Management
- No automatic cleanup of expired entries (entries remain until refresh)
- Manual invalidation available for memory pressure scenarios
- Consider periodic cache cleanup in long-running applications

## Testing Strategy

### Unit Tests (`test_cache.py`)
- Name normalization logic
- Cache entry expiration
- Index operations
- ASCII folding

### Integration Tests (`test_client_cache.py`)
- Client cache method behavior
- HTTP cache validation
- Conditional request handling
- Async client functionality

### Test Data
- Mock site and measurement responses
- Simulated HTTP cache headers
- Expiration scenarios

## Future Enhancements

### Planned Features
1. **Thread Safety**: Concurrent access support
2. **Persistent Cache**: Optional disk-based caching
3. **Cache Statistics**: Hit/miss ratios, performance metrics
4. **Memory Limits**: LRU eviction for memory-constrained environments
5. **Background Refresh**: Proactive cache updates

### Potential Optimizations
1. **Compressed Storage**: Reduce memory footprint for large datasets
2. **Incremental Updates**: Partial cache updates instead of full refresh
3. **Smart Prefetching**: Predict and cache likely-needed data
4. **Cache Warming**: Background population of frequently-accessed entries