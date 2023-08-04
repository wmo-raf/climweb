# Frequently Asked Questions (FAQs)

**1. What technologies is the CMS Built on?**

>The CMS, along with its various components, is **completely open-source** and developed on the [WMO RAF GitHub account](https://github.com/orgs/wmo-raf). This implies that the institution will have **unrestricted access to the source code**, allowing them to identify and report any bugs, request new features, and even actively contribute to the development of the codebase. This open approach encourages collaboration and fosters a sense of ownership and involvement within the institution.

**2. Who will manage the CMS Content?**

>The **NMHS installing the CMS and its components will be fully responsible** for inputting and managing the content that goes into the CMS, from their side. This means that they take the instance of the code and run it, without anyone else having access to the operational instance, unless authorized to do so.

**3. What if an NMHS already has a website?**
>In cases where an NMHS already has an existing website but is interested in testing the new CMS, they have the option to install and run it **concurrently with their existing system** for a specific duration. This allows them to thoroughly evaluate and experience the functionalities offered by the new CMS. Once the NMHS is satisfied and comfortable with the new CMS, a phased approach can be adopted to gradually transition and fully migrate their website to the new CMS. This ensures a smooth and well-managed transition process.

**4. What does ‘CMS’ mean?**
>The term ‘CMS’, as used in this document, refers to **all the components** working together to have a running website, more especially on managing the website content. Read more about the CMS Key functionalities https://github.com/wmo-raf/nmhs-cms/wiki 

**5. What with NMHSs services that do not have IT people**
>A fundamental aspect considered during the design and development phase of the CMS was to establish a clear and well-defined system for managing content and page structure. This involved creating a **user-friendly interface with a modern design and intuitive features,** aimed at providing users with a seamless and enjoyable experience. The objective was to enable users to easily locate content and utilize the CMS **without the need for specialized IT skills**.

**6. Security risks?**
>The CMS, which is being built using open-source technologies, benefits from the advantage of having a community of developers who actively contribute to enhancing its security and stability. Furthermore, the CMS offers robust **support for secure authentication mechanisms**, including username/password authentication, integration with third-party authentication systems such as OAuth, and the ability to implement custom authentication backends. Additionally, the CMS performs **regular backups to safeguard the website's data** and enable its restoration in case of data loss. The NMHS are encouraged to share **only the final products** intended for the public.


**7. Where is it hosted?**
>The CMS is deployed **at the National Meteorological and Hydrological Service (NMHS) level,** utilising either **cloud-based infrastructure or on-premises servers**. Please refer to the provided **server specifications** for more details on the hosting environment.

**8. Is WMO RAF managing or handing over completely?**
>The **NMHSs independently manage all components of the CMS in a decentralized manner** at the departmental level. The CMS includes an administrative role (superuser) that possesses complete privileges to access all components of the system. Further information regarding users and roles can be found at (https://github.com/wmo-raf/nmhs-cms/wiki/Manage-Users-and-Roles). It is important to note that WMO RAF does not have involvement in managing the CMS, as its administration and control lie solely with the NMHSs.
While WMO RAF does not directly manage the CMS, it does offer valuable support to NMHSs by **providing training and guidance** on the proper management of the CMS. WMO's role is to assist NMHSs in acquiring the necessary knowledge and skills to effectively handle and maintain the CMS. This training and guidance aim to empower NMHSs in utilizing the CMS to its full potential and ensuring optimal performance and functionality.

**9. Training and capacity building: how will it be done?**
>WMO RAF will conduct training sessions for the CMS, which can be arranged in **either face-to-face or online formats**. Comprehensive **training materials**, including user guides (https://github.com/wmo-raf/nmhs-cms/wiki) and developer guides (https://github.com/wmo-raf/nmhs-cms), are also available. The training sessions will be specifically targeted towards designated **departmental focal points **responsible for each component of the CMS. This approach ensures that the training is tailored to meet the specific needs and roles within the NMHS, enabling efficient knowledge transfer and effective utilization of the CMS.

**10. What about NMHS that want to migrate their website? What provision for migration?** 
>The migration process will commence by initially **identifying the current content of the pages, as well as identifying additional pages that may be relevant and determining any obsolete content**. Moreover, recommendations will be provided regarding optimal practices pertaining to wording, images, colors, and other related aspects. The manual migration of each page will be conducted in collaboration with departmental focal points to ensure efficient coordination.

**11. What support will be offered by WMO RAF?**
>Support on the operationalization of the CMS cuts across:
>* Assessing Quality and interactivity of existing NMHS website 
>* Approach and present the CMS to the NMHS. Integrate suggested feedback 
>* Identify departmental focal points for CMS coordination including overall CMS administrator 
>* Installation and setup of CMS in-premise servers/cloud servers 
>* Provision one-on-one training and capacity building to departmental focal points on configuration and customization of the CMS and Website 
>* Provision of learning materials, documentations, and guides of the CMS 
>* Follow-up support in troubleshooting and resolving technical bugs  

>This also includes the implementation of CAP Alerts, Georeferenced data visualization, email marketing, events, surveys, and user analytics integration.

**12. How does the CMS work in low internet connectivity**
>The CMS is optimized for low bandwidth scenarios. This involves the minimisation of the use of large images, videos or heavy media files that might consume a significant amount of bandwidth.
The CMS also supports **caching mechanisms** that can help reduce the load on the server and improve the website’s performance. By enabling caching, static content can be stored on the user's device, reducing the need for repeated downloads, and enhancing the experience on low bandwidth connections.

**13. Geo-referenced data visualization: What data sources and formats are supported?**
>An essential feature provided by the CMS is its capability to **facilitate interactive visualization of georeferenced data**. This includes the ability to upload and visualize gridded data in formats such as NetCDF and GeoTIFF, as well as vector data in the form of points and polygons. The CMS also supports the integration of CAP Alerts and enables the inclusion of data from external Web Map Service (WMS) sources for comprehensive data visualization.

**14. Can they use the CAP editor alone?**
>The CAP Editor has been developed to be flexible in its deployment options. It can be run independently as a **standalone application**, which is accessible at https://github.com/wmo-raf/cap-editor. Alternatively, it can be fully **integrated into the CMS**, providing seamless management of CAP Alerts within the CMS environment. More information about the integration and usage can be found at https://github.com/wmo-raf/nmhs-cms/wiki/Manage-CAP-Alerts.