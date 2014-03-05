var app = angular.module('SimpleAddress', ['ui.bootstrap']);

app.filter('startFrom', function() {
    return function(input, start) {
        if(input) {
            start = +start;
            return input.slice(start);
        }
        return [];
    }
});

function AddressListCtrl($scope, $timeout, $http, $modal) {
    // Any alerts that have happened on the page
    $scope.alerts = [];
    
    // Hold your addresses
    $scope.addresses = [];
    
    // Set up filtering and pagination vars
    $scope.totalItems = 0;
    $scope.currentPage = 1;
    $scope.noOfPages = 1;
    // max number of pages to display
    $scope.maxSize = 5;
    // number per page
    $scope.entryLimit = 10;
    
    $scope.setPage = function(pageNo) {
        $scope.currentPage = pageNo;
    };

    $scope.filter = function() {
        $timeout(function() {
            // wait for 'filtered' to be changed
            $scope.noOfPages = Math.ceil($scope.filtered.length/$scope.entryLimit);
            $scope.totalItems = $scope.filtered.length;
        }, 10);
    };
    
    // Currently look for first and last name, along with spouse
    $scope.mySearch = function(address) {
        var re = new RegExp($scope.search, 'i');
        return re.test(address.first_name + " " + address.last_name) || re.test(address.spouse);
    };
    
    $http.get('addresses').success(function(addresses)
        {
            $scope.addresses = addresses;
            $scope.noOfPages = Math.ceil($scope.addresses.length/$scope.entryLimit);
            $scope.totalItems = $scope.addresses.length;
        }).error(function(data, status, headers, config)
        {
            $scope.addAlert("Failure getting addresses", status);
        });

    $scope.change = function(address)
    {
        $http.put('addresses', address).error(function(data, status, headers, config)
            {
                $scope.addAlert("Failure saving address", status);
            });
    };

    $scope.create = function()
    {
        var newAddress =
        {
            "first_name": $scope.newaddress.first_name,
            "last_name": $scope.newaddress.last_name,
            "spouse": $scope.newaddress.spouse,
            "email_address": $scope.newaddress.email_address,
            "street_1": $scope.newaddress.street_1,
            "street_2": $scope.newaddress.street_2 || '',
            "city": $scope.newaddress.city,
            "state": $scope.newaddress.state,
            "zip": $scope.newaddress.zip,
            "country": $scope.newaddress.country || '',
            "home_phone": $scope.newaddress.home_phone,
            "mobile_phone": $scope.newaddress.mobile_phone,
            "relationship": $scope.newaddress.relationship,
            "title": $scope.newaddress.title,
            "children": $scope.newaddress.children,
            "label_name": $scope.newaddress.label_name
        };

        $http.post('addresses', newAddress).success(function(data, status, headers, config)
            {
                newAddress._id = data._id;
                $scope.addresses.push(newAddress);
            }).error(function(data, status, headers, config)
            {
                $scope.addAlert("Failure creating address", status);
            });
    };

    $scope.open = function(editAddress)
    {
        var modalData =
            {
                templateUrl: 'editContent.html',
                controller: ModalEditCtrl,
                resolve: {
                    address: function()
                        {
                            return editAddress;
                        }
                }
            };
        var modalInstance = $modal.open(modalData);
        modalInstance.result.then(function (savedAddress)
            {
                $scope.change(savedAddress);
            });
    };

    $scope.remove = function(removeAddress)
    {
        var modalData =
            {
                templateUrl: 'removeDialog.html',
                controller: ModalRemoveCtrl,
            };
        var modalInstance = $modal.open(modalData);
        modalInstance.result.then(function ()
            {
                $http.delete('addresses/' + removeAddress._id).success(function(data, status, headers, config)
                    {
                        var addresses = $scope.addresses;
                        var index = addresses.indexOf(removeAddress);
                        addresses.splice(index, 1);
                    }).error(function(data, status, headers, config)
                    {
                        $scope.addAlert("Failure deleting address", status);
                    });
                });
    };

    $scope.addAlert = function(message, status) {
        // Put in custom messages for the alerts here if desired
        if (status !== null)
        {
            message += ": ";
            
            switch (status)
            {
                case 500:
                    message += "Internal Server Error";
                    break;
                case 400:
                    message += "Bad Request";
                    break;
                default:
                    message += status;
                    break;
            }
        }
        $scope.alerts.push({msg: message});
    };

  $scope.closeAlert = function(index) {
        $scope.alerts.splice(index, 1);
  };
}

var ModalEditCtrl = function ($scope, $modalInstance, address)
{
    $scope.address = address;

    $scope.ok = function ()
    {
        $modalInstance.close($scope.address);
    };

    $scope.cancel = function ()
    {
        $modalInstance.dismiss('cancel');
    };
};

var ModalRemoveCtrl = function($scope, $modalInstance)
{
    $scope.ok = function()
    {
        $modalInstance.close();
    };

    $scope.cancel = function ()
    {
        $modalInstance.dismiss('cancel');
    };
};