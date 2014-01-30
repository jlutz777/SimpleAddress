var AddressListCtrl = function($scope, $http, $modal)
{
    $http.get('addresses').success(function(addresses)
        {
            $scope.addresses = addresses;
        }).error(function(err)
        {
            alert(err);
        });

    $scope.change = function(address)
    {
        $http.put('addresses', address);
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
                $scope.addresses.push(newAddress);
                newAddress._id = data._id;
            }).error(function(data, status, headers, config)
            {
                alert("Failure creating with status " + status);
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
                        alert("Failure deleting with status " + status);
                    });
                });
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
