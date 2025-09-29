from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from whurl.schemas.responses.measurement_list import MeasurementListResponse
from whurl.schemas.responses.site_list import SiteListResponse
import re
import time
import unicodedata

"""Domain-layer cache for canonical site and measurement lists.

This module provides an in-memory cache for storing canonical, unfiltered
site and measurement lists as normalized indexes. It supports fast existence
checks, index queries, and HTTP cache validation via ETags and Last-Modified
headers.
"""




@dataclass
class CacheEntry:
    """Represents a cached entry with metadata."""
    
    data: Any
    timestamp: datetime
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    expires: Optional[datetime] = None

    @property
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.expires is None:
            return False
        return datetime.now(datetime.UTC) > self.expires


def normalize_name(name: str, ascii_fold: bool = False) -> str:
    """Normalize site/measurement names for consistent indexing.
    
    Parameters
    ----------
    name : str
        The name to normalize.
    ascii_fold : bool, default False
        Whether to fold Unicode characters to ASCII equivalents.
        
    Returns
    -------
    str
        Normalized name.
    """
    if not name:
        return ""
    
    # Strip whitespace and convert to lowercase
    normalized = name.strip().lower()
    
    # Collapse multiple whitespace into single spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    
    if ascii_fold:
        # Fold Unicode characters to ASCII equivalents
        normalized = unicodedata.normalize('NFKD', normalized)
        normalized = normalized.encode('ascii', 'ignore').decode('ascii')
    
    return normalized


class DomainCache:
    """Domain-layer cache for canonical site and measurement lists.
    
    This cache stores full site and measurement lists as normalized indexes
    and provides fast existence checks and metadata queries.
    
    Parameters
    ----------
    default_ttl : timedelta, default timedelta(hours=1)
        Default time-to-live for cached entries.
    ascii_fold : bool, default False
        Whether to fold Unicode names to ASCII for normalization.
    """
    
    def __init__(
        self, 
        default_ttl: timedelta = timedelta(hours=1),
        ascii_fold: bool = False
    ):
        self.default_ttl = default_ttl
        self.ascii_fold = ascii_fold
        
        # Site cache: normalized_name -> site_data
        self._sites: Dict[str, Any] = {}
        # Site index: site_id -> site_data (if ID is available)
        self._sites_by_id: Dict[str, Any] = {}
        # Original name -> normalized_name mapping
        self._site_name_mapping: Dict[str, str] = {}
        
        # Measurement cache: (site_name, measurement_name) -> measurement_data
        self._measurements: Dict[tuple, Any] = {}
        # Measurement index by site
        self._measurements_by_site: Dict[str, List[Any]] = {}
        # Original measurement name -> normalized name mapping
        self._measurement_name_mapping: Dict[str, str] = {}
        
        # Cache metadata
        self._sites_cache_entry: Optional[CacheEntry] = None
        self._measurements_cache_entry: Optional[CacheEntry] = None

    def refresh_sites(
        self, 
        response: SiteListResponse,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None
    ) -> None:
        """Refresh the sites cache with new data.
        
        Parameters
        ----------
        response : SiteListResponse
            The site list response to cache.
        etag : str, optional
            ETag header value from HTTP response.
        last_modified : str, optional
            Last-Modified header value from HTTP response.
        """
        # Clear existing site data
        self._sites.clear()
        self._sites_by_id.clear()
        self._site_name_mapping.clear()
        
        # Populate site indexes
        for site in response.site_list:
            original_name = site.name
            normalized_name = normalize_name(original_name, self.ascii_fold)
            
            # Store site data by normalized name
            self._sites[normalized_name] = site
            
            # Store original -> normalized mapping
            self._site_name_mapping[original_name] = normalized_name
            
            # Store by ID if available (though not in current Site model)
            # This is future-proofing for potential site ID fields
            
        # Update cache metadata
        expires = datetime.now(datetime.UTC) + self.default_ttl
        self._sites_cache_entry = CacheEntry(
            data=response,
            timestamp=datetime.now(datetime.UTC),
            etag=etag,
            last_modified=last_modified,
            expires=expires
        )

    def refresh_measurements(
        self,
        response: MeasurementListResponse,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None
    ) -> None:
        """Refresh the measurements cache with new data.
        
        Parameters
        ----------
        response : MeasurementListResponse
            The measurement list response to cache.
        etag : str, optional
            ETag header value from HTTP response.
        last_modified : str, optional
            Last-Modified header value from HTTP response.
        """
        # Clear existing measurement data
        self._measurements.clear()
        self._measurements_by_site.clear()
        self._measurement_name_mapping.clear()
        
        # Populate measurement indexes
        for data_source in response.data_sources:
            site_name = data_source.site
            normalized_site_name = normalize_name(site_name, self.ascii_fold)
            
            site_measurements = []
            
            for measurement in data_source.measurements:
                original_name = measurement.name
                normalized_name = normalize_name(original_name, self.ascii_fold)
                
                # Store measurement by (normalized_site, normalized_measurement)
                cache_key = (normalized_site_name, normalized_name)
                self._measurements[cache_key] = measurement
                
                # Store original -> normalized mapping
                full_original_name = f"{site_name}::{original_name}"
                full_normalized_name = f"{normalized_site_name}::{normalized_name}"
                self._measurement_name_mapping[full_original_name] = full_normalized_name
                
                site_measurements.append(measurement)
            
            # Store measurements by site
            self._measurements_by_site[normalized_site_name] = site_measurements
        
        # Update cache metadata
        expires = datetime.now(datetime.UTC) + self.default_ttl
        self._measurements_cache_entry = CacheEntry(
            data=response,
            timestamp=datetime.now(datetime.UTC),
            etag=etag,
            last_modified=last_modified,
            expires=expires
        )

    def list_all_sites(self) -> List[Any]:
        """Get all cached sites.
        
        Returns
        -------
        List[Any]
            List of all cached site objects.
        """
        return list(self._sites.values())

    def check_for_site(self, name: str) -> bool:
        """Check if a site exists in the cache.
        
        Parameters
        ----------
        name : str
            Site name to check.
            
        Returns
        -------
        bool
            True if site exists in cache, False otherwise.
        """
        normalized_name = normalize_name(name, self.ascii_fold)
        return normalized_name in self._sites

    def get_site(self, name: str) -> Optional[Any]:
        """Get site metadata by name.
        
        Parameters
        ----------
        name : str
            Site name to retrieve.
            
        Returns
        -------
        Optional[Any]
            Site metadata object if found, None otherwise.
        """
        normalized_name = normalize_name(name, self.ascii_fold)
        return self._sites.get(normalized_name)

    def list_all_measurements(self) -> List[Any]:
        """Get all cached measurements.
        
        Returns
        -------
        List[Any]
            List of all cached measurement objects.
        """
        all_measurements = []
        for measurements in self._measurements_by_site.values():
            all_measurements.extend(measurements)
        return all_measurements

    def get_measurements_for_site(self, site_name: str) -> List[Any]:
        """Get all measurements for a specific site.
        
        Parameters
        ----------
        site_name : str
            Name of the site.
            
        Returns
        -------
        List[Any]
            List of measurement objects for the site.
        """
        normalized_site_name = normalize_name(site_name, self.ascii_fold)
        return self._measurements_by_site.get(normalized_site_name, [])

    @property
    def sites_cache_valid(self) -> bool:
        """Check if the sites cache is valid (not expired)."""
        if self._sites_cache_entry is None:
            return False
        return not self._sites_cache_entry.is_expired

    @property
    def measurements_cache_valid(self) -> bool:
        """Check if the measurements cache is valid (not expired)."""
        if self._measurements_cache_entry is None:
            return False
        return not self._measurements_cache_entry.is_expired

    def get_sites_etag(self) -> Optional[str]:
        """Get the ETag for the cached sites data."""
        if self._sites_cache_entry is None:
            return None
        return self._sites_cache_entry.etag

    def get_sites_last_modified(self) -> Optional[str]:
        """Get the Last-Modified timestamp for cached sites data."""
        if self._sites_cache_entry is None:
            return None
        return self._sites_cache_entry.last_modified

    def get_measurements_etag(self) -> Optional[str]:
        """Get the ETag for the cached measurements data."""
        if self._measurements_cache_entry is None:
            return None
        return self._measurements_cache_entry.etag

    def get_measurements_last_modified(self) -> Optional[str]:
        """Get the Last-Modified timestamp for cached measurements data."""
        if self._measurements_cache_entry is None:
            return None
        return self._measurements_cache_entry.last_modified

    def invalidate_sites(self) -> None:
        """Invalidate the sites cache."""
        self._sites.clear()
        self._sites_by_id.clear()
        self._site_name_mapping.clear()
        self._sites_cache_entry = None

    def invalidate_measurements(self) -> None:
        """Invalidate the measurements cache."""
        self._measurements.clear()
        self._measurements_by_site.clear()
        self._measurement_name_mapping.clear()
        self._measurements_cache_entry = None

    def invalidate_all(self) -> None:
        """Invalidate all cached data."""
        self.invalidate_sites()
        self.invalidate_measurements()