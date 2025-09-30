import React, { useState, useEffect } from 'react';
import { Loader2, MapPin, Globe, Building2, DollarSign, Star, CheckCircle, AlertCircle } from 'lucide-react';
import httpClient from '../api/httpClient';

interface ServiceProvider {
  name: string;
  type: string;
  local: boolean;
  description: string;
  key_considerations: string;
  estimated_cost: string;
  contact_method: string;
  specialties: string;
  category: string;
}

interface ServiceProviderTableProps {
  taskContext: string;
  businessContext: {
    industry?: string;
    location?: string;
    business_type?: string;
    business_name?: string;
  };
  onProviderSelect?: (provider: ServiceProvider) => void;
  className?: string;
  cachedData?: any;
  isLoading?: boolean;
}

const ServiceProviderTable: React.FC<ServiceProviderTableProps> = ({
  taskContext,
  businessContext,
  onProviderSelect,
  className = "",
  cachedData,
  isLoading = false
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [providers, setProviders] = useState<ServiceProvider[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedLocation, setSelectedLocation] = useState<string>('all');

  useEffect(() => {
    if (cachedData) {
      // Use cached data
      const providerData = cachedData.result.providers.provider_table.original_table;
      const allProviders: ServiceProvider[] = [];
      
      // Flatten providers from all categories
      if (providerData && providerData.provider_tables) {
        Object.entries(providerData.provider_tables).forEach(([categoryName, category]: [string, any]) => {
          if (category && category.providers) {
            // Add category name to each provider
            const providersWithCategory = category.providers.map((provider: any) => ({
              ...provider,
              category: categoryName
            }));
            allProviders.push(...providersWithCategory);
          }
        });
      }
      
      // Extract categories from the API response
      const availableCategories = Object.keys(providerData.provider_tables || {});
      
      setProviders(allProviders);
      setCategories(availableCategories);
      setLoading(false);
    } else if (!isLoading) {
      // Only fetch if not loading and no cached data
      fetchProviders();
    }
  }, [taskContext, businessContext, cachedData, isLoading]);

  const fetchProviders = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('sb_access_token');
      if (!token) {
        setError('Authentication required');
        return;
      }

      const response = await httpClient.post('/specialized-agents/provider-table', {
        task_id: taskContext, // Use task_id instead of task_context
        business_context: businessContext,
        location: businessContext.location
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if ((response.data as any).success) {
        const providerData = (response.data as any).result.providers.provider_table.original_table;
        const allProviders: ServiceProvider[] = [];
        
        // Flatten providers from all categories
        if (providerData && providerData.provider_tables) {
          Object.entries(providerData.provider_tables).forEach(([categoryName, category]: [string, any]) => {
            if (category && category.providers) {
              // Add category name to each provider
              const providersWithCategory = category.providers.map((provider: any) => ({
                ...provider,
                category: categoryName
              }));
              allProviders.push(...providersWithCategory);
            }
          });
        }
        
        // Extract categories from the API response
        const availableCategories = Object.keys(providerData.provider_tables || {});
        
        setProviders(allProviders);
        setCategories(availableCategories);
      } else {
        setError((response.data as any).message || 'Failed to fetch service providers');
      }
    } catch (err: any) {
      console.error('Error fetching providers:', err);
      setError(err.response?.data?.message || 'Failed to fetch service providers');
    } finally {
      setLoading(false);
    }
  };

  const getFilteredProviders = () => {
    let filtered = providers;

    if (selectedCategory !== 'all') {
      filtered = filtered.filter(provider => 
        provider.category === selectedCategory
      );
    }

    if (selectedLocation !== 'all') {
      if (selectedLocation === 'local') {
        filtered = filtered.filter(provider => provider.local);
      } else if (selectedLocation === 'online') {
        filtered = filtered.filter(provider => !provider.local);
      }
    }

    return filtered;
  };


  const filteredProviders = getFilteredProviders();

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Building2 className="h-5 w-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Service Provider Table</h2>
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            Local & Online
          </span>
        </div>
        <p className="text-sm text-gray-600 mt-1">
          Find credible service providers for your business needs.
        </p>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full max-w-md p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Categories</option>
              {categories.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="w-full max-w-md p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Locations</option>
              <option value="local">Local Only</option>
              <option value="online">Online Only</option>
            </select>
          </div>
        </div>

        {/* Loading State */}
        {(loading || isLoading) && (
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500 mx-auto mb-2" />
              <p className="text-gray-600">Loading service providers...</p>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-500" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        )}

        {/* Providers Grid */}
        {!loading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredProviders.map((provider, index) => (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => onProviderSelect?.(provider)}
              >
                {/* Provider Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 mb-1">{provider.name}</h3>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-600">{provider.type}</span>
                      {provider.local && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          <MapPin className="h-3 w-3" />
                          Local
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Description */}
                <p className="text-sm text-gray-700 mb-3 line-clamp-2">{provider.description}</p>

                {/* Specialties */}
                {provider.specialties && (
                  <div className="mb-3">
                    <div className="text-xs font-medium text-gray-600 mb-1">Specialties:</div>
                    <div className="flex flex-wrap gap-1">
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {provider.specialties}
                      </span>
                    </div>
                  </div>
                )}

                {/* Key Considerations */}
                {provider.key_considerations && (
                  <div className="mb-3">
                    <div className="text-xs font-medium text-gray-600 mb-1">Key Considerations:</div>
                    <p className="text-sm text-gray-700">{provider.key_considerations}</p>
                  </div>
                )}

                {/* Contact Method */}
                {provider.contact_method && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Globe className="h-4 w-4" />
                      <span>{provider.contact_method}</span>
                    </div>
                  </div>
                )}

                {/* Pricing */}
                {provider.estimated_cost && (
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <div className="flex items-center gap-2 text-sm">
                      <DollarSign className="h-4 w-4 text-green-600" />
                      <span className="font-medium text-gray-900">{provider.estimated_cost}</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* No Results */}
        {!loading && !error && filteredProviders.length === 0 && (
          <div className="text-center py-8">
            <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Providers Found</h3>
            <p className="text-gray-600">
              Try adjusting your filters or check back later for more providers.
            </p>
          </div>
        )}

        {/* Results Summary */}
        {!loading && !error && filteredProviders.length > 0 && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <span className="font-medium text-gray-900">
                Found {filteredProviders.length} service provider{filteredProviders.length !== 1 ? 's' : ''}
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              Click on any provider to get more details or contact information.
            </p>
          </div>
        )}

        {/* Business Context */}
        <div className="pt-4 border-t border-gray-200">
          <h3 className="font-semibold text-gray-900 mb-2">Business Context</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Business:</span>
              <span className="font-medium ml-2">{businessContext.business_name || 'Not specified'}</span>
            </div>
            <div>
              <span className="text-gray-600">Industry:</span>
              <span className="font-medium ml-2">{businessContext.industry || 'Not specified'}</span>
            </div>
            <div>
              <span className="text-gray-600">Location:</span>
              <span className="font-medium ml-2">{businessContext.location || 'Not specified'}</span>
            </div>
            <div>
              <span className="text-gray-600">Type:</span>
              <span className="font-medium ml-2">{businessContext.business_type || 'Not specified'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ServiceProviderTable;