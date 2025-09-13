### File Name
Person.cs

### Logic
1. Define a class named `Person`.
2. Declare the following properties within the `Person` class:
   1. `PersonId`: an integer property that can be initialized but not changed once set.
   2. `Username`: a nullable string property that can be both retrieved and modified.
   3. `Email`: a nullable string property that can be both retrieved and modified.
   4. `Bio`: a nullable string property that can be both retrieved and modified.
   5. `Image`: a nullable string property that can be both retrieved and modified.
   6. `ArticleFavorites`: a list of `ArticleFavorite` objects, initialized but not modifiable after creation.
   7. `Following`: a list of `FollowedPeople` objects, initialized but not modifiable after creation.
   8. `Followers`: a list of `FollowedPeople` objects, initialized but not modifiable after creation.
   9. `Hash`: a byte array property that can be both retrieved and modified.
   10. `Salt`: a byte array property that can be both retrieved and modified.

### Summary
The file `Person.cs` defines a `Person` class that serves as a model for a user within the application. It encapsulates various attributes relevant to a user account, such as identification, personal information, social relationships (followers and following), and credentials for authentication (hash and salt). The use of properties includes both mutable and immutable fields, catering to the application’s requirements for handling user details and maintaining data integrity. The presence of lists for holding favorites and social connections suggests that the application is designed to manage user interactions within a social context, likely related to articles or content.