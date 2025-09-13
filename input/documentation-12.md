### File Name
ArticlesController.cs

### Logic
1. **Get Articles**
   - Receive parameters: `tag`, `author`, `favorited`, `limit`, `offset`, `cancellationToken`.
   - Invoke `mediator.Send` with a new `List.Query` using the received parameters.
   - Return a `Task<ArticlesEnvelope>`.

2. **Get Articles Feed**
   - Receive parameters: `tag`, `author`, `favorited`, `limit`, `offset`, `cancellationToken`.
   - Invoke `mediator.Send` with a new `List.Query` using the received parameters and set `IsFeed` to true.
   - Return a `Task<ArticlesEnvelope>`.

3. **Get Article Details**
   - Receive parameters: `slug`, `cancellationToken`.
   - Invoke `mediator.Send` with a new `Details.Query` using the received `slug`.
   - Return a `Task<ArticleEnvelope>`.

4. **Create Article**
   - Receive parameters: `command`, `cancellationToken`.
   - Invoke `mediator.Send` with the received `command`.
   - Return a `Task<ArticleEnvelope>`.

5. **Edit Article**
   - Receive parameters: `slug`, `model`, `cancellationToken`.
   - Invoke `mediator.Send` with a new `Edit.Command` using the received `model` and `slug`.
   - Return a `Task<ArticleEnvelope>`.

6. **Delete Article**
   - Receive parameters: `slug`, `cancellationToken`.
   - Invoke `mediator.Send` with a new `Delete.Command` using the received `slug`.
   - Return a `Task`.

### Summary
The `ArticlesController.cs` file is a part of the Conduit application that handles HTTP requests related to articles. It provides functionality to fetch a list of articles, obtain a specific article's details, create new articles, update existing articles, and delete articles. The controller serves as an intermediary between client requests and the application's business logic, using the Mediator pattern to delegate tasks for processing and retrieving data associated with articles. The methods support handling different parameters for filtering articles and managing article-related operations in an organized manner.