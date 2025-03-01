resource storageAccount 'Microsoft.Storage/storageAccounts@2021-06-01' = {
  name: 'myuniquelabstsdf430854'
  location: resourceGroup().location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
}
