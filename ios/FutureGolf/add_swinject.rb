#!/usr/bin/env ruby

require 'xcodeproj'

# Open the project
project_path = './FutureGolf.xcodeproj'
project = Xcodeproj::Project.open(project_path)

# Create the Swinject package reference
swinject_url = 'https://github.com/Swinject/Swinject.git'
swinject_version = '2.9.1'

# Check if Swinject is already added
existing_package = project.root_object.package_references.find { |ref| ref.repositoryURL == swinject_url }

if existing_package.nil?
  # Add the package reference
  package_ref = project.new(Xcodeproj::Project::Object::XCRemoteSwiftPackageReference)
  package_ref.repositoryURL = swinject_url
  package_ref.requirement = {
    'kind' => 'upToNextMajorVersion',
    'minimumVersion' => swinject_version
  }
  
  project.root_object.package_references << package_ref
  
  # Add the package product dependency to the main target
  main_target = project.targets.find { |t| t.name == 'FutureGolf' }
  
  if main_target
    package_product = project.new(Xcodeproj::Project::Object::XCSwiftPackageProductDependency)
    package_product.package = package_ref
    package_product.product_name = 'Swinject'
    
    main_target.package_product_dependencies << package_product
  end
  
  # Save the project
  project.save
  puts "✅ Swinject package added successfully!"
else
  puts "ℹ️ Swinject package already exists in the project"
end