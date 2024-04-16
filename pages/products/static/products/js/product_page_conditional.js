window.addEventListener('DOMContentLoaded', (event) => {

    const serviceInput = document.getElementById('id_service');

    const otherServicesContainer = document.getElementById('panel-child-content-other_services-section');

    const otherServicesWrapper = document.getElementById('id_other_services');
    const otherServices = otherServicesWrapper.querySelectorAll('input[type="checkbox"]');
    const serviceInputValue = serviceInput.value;

    const updateOtherServices = (selectedService) => {
        otherServices.forEach((service) => {
            const serviceValue = service.value;
            const serviceWrapper = service.closest('div');

            if (serviceValue === selectedService) {
                service.checked = false;
                serviceWrapper.style.display = 'none';
            } else {
                serviceWrapper.style.display = 'block';
            }
        });
    }

    if (!serviceInputValue) {
        otherServicesContainer.style.display = 'none';
    } else {
        updateOtherServices(serviceInputValue);
    }


    serviceInput.addEventListener('change', (event) => {
        const selectedService = serviceInput.value;

        if (selectedService) {
            otherServicesContainer.style.display = 'block';
        }

        updateOtherServices(selectedService);
    });


});
