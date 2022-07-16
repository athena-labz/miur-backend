# Crowdfunding API
We'll have two separate processes for the crowdfunding application. One will handle cardano transactions only (athena api), the other will handle the database transactions (this project - crowdfunding api).

Athena API will not be called by the front-end directly, but by this API (crowdfunding API) whenever we need to create some transaction or query blockchain information related to athena.

## Table of Contents
* [Architecture](#architecture)
    * [Health](#health)
    * [Join Athena](#join-athena)
    * [Confirm Submitted](#confirm-submitted)
    * [Get User Account](#get-user-account)
    * [Create Project](#projects/create)
    * [Get Project](#get-project)
    * [Get Projects](#get-projects)
    * [Search Projects](#search-projects)
    * [Start Project](#start-project)
    * [Give Up Project](#give-up-project)
    * [Finish Deliverable](#finish-deliverable)
    * [Contest Deliverable](#contest-deliverable)
    * [Fund Project](#fund-project)
    * [Mark Deliverable As Completed](#mark-deliverable-as-completed)
    * [Mark Deliverable As Failed](#mark-deliverable-as-failed)
    * [Finish Project](#finish-project)
    * [Get Disputes](#get-disputes)
* [Example](#example)
* [Endpoints](#endpoints)
* [Notes](#notes)


## Architecture
See openapi-spec for more details about each endpoint.

### Health
Whether the API is working right now or not. Does basic checks such as if the DB is working.

### Join Athena
Receives user address (and public key hash if we aren't able to figure it out) and returns the "create-account" transaction CBOR.

### Confirm Submitted
Receives a transaction hash and confirms this transaction was submitted. It's purpose is mainly user responsiveness and it shouldn't be treated as a proof that the transaction was submitted since a user can fake this endpoint request.

### Get User Account
Return user basic information, such as projects, disputes, history and if the account is authenticated on-chain. User account information should be public, so we shouldn't need to verify the user identity here.

### Create project
Each project will have it's own address for receiving funds. In the testing phase (2022 Q2 & Q3), a key will be created for each project and saved in the databased (encrypted with a key that should be located in this repo). In the production phase, this will be a script that will receive the following parameters:

* Deadline
* Contract NFT

And the datum should keep track of who funded the script with his public key hash (@Funder@).

Project proposer can always go back and give up the project, giving the users back their funds. We should have some collateral, though, to compensate users for their time if that happens.

Problem is how do we keep track of every user who contributed. (Probably see them individually since we don't care about target anymore).

If @Deadline@ is reached user needs to transfer the funds to the script with @Contract NFT@.

After funds are collected from a user contract, he should receive some kind of receipt NFT so he can redeem the funds later if anything goes wrong with the project.

The ultimate goal for Athena (making it completely decentralised) is to have a script that will collect user funds, the one just described above, and have a script for signing a contract with the project proposer [and collecting the funds back if anything goes wrong] called script representative which should be a minting policy that will need to burn a certain token).

### Get Project
Returns detailed information about a specific project

### Get projects
Returns basic information about all projects (should be paginated).

### Search projects
Same thing as get projects (get's basic information from projects), but filters them based on certain parameters, including user.


The following endpoints will query athena api to confirm a transaction, if this transaction is on-chain, they should update our DB accordingly.

### Start project
Update our database to indicate that the project creator received the funds and should be start working on his deliverables. At the same time, make a request to athena api to create a contract between the platform and this user and return the CBOR of this transaction.

### Give Up Project
Update our database to indicate that the project creator gave up the project and decided to give the funds back to the users. This should be allowed even before the deadline. At the same time, make a request to athena api to create a contract between the platform and this user and return the CBOR of this transaction.

### Finish deliverable
Create deliverable request in the database, which shall be analyzed by the mediators. Additionally return the CBOR of the transaction that does that.

### Contest deliverable
If deadline passed and deliverable wasn't completed by project proposer, users should be able to get their funds back (at least the funds that remain). This is just a dispute, though, the mediator needs to decide whether it's valid or not. Return the CBOR for this transaction after requesting it from athena api.

### Fund project
There should be a user funds table with all users who contributed to a project. This is useful because we need to give user feedback about the projects he contributed to.

So this endpoint returns the CBOR of the fund project transaction and updates the database to include that this user funded this project.

### Mark deliverable as completed
After mediator has decided in favour of a project proposer (who supposedly finished a deliverable), add new row to our deliverables table indicating that this specific deliverable was marked as completed. Return correspondent transaction cbor (get it from athena api).

In athena v1 we should't care about mediator resolution disputes.

### Mark deliverable as failed
If a mediator decides to accept the "contest deliverable" request, funds should be given back to the users who contributed. Return correspondent transaction cbor (get it from athena api).

(How do we know who contributed?)
(Every time a user contributes we could mint a token with the project NFT token name)

### Finish project
After all deliverables were completed, both parties (platform and project proposer) can leave the contract. Return correspondent transaction cbor (get it from athena api).

### Get Disputes
Return a list of all existing disputes for a specific mediator to resolve.

## Example

Let's assume we have the following participants:
* Alice - Student - Wants to propose a cool school project
* Bob - Student - Wants to support Alices project
* Charlie - Teacher - Needs to make sure her students are doing completing delivering their projects

*Alice*

### Signing in / Signing Up
Should be automatic. As soon as alice lands on main page, front-end should request for user info based on his address. We can, however, add a field on profile where the user can input additional information.

### Joining Athena
Before Alice can create a project, she needs to join athena. This process is described by the following flow:

* Alice lands on main page
* One of
    * Clicks on profile
        * /user/<bech32_addr> (Get User Info)
    * Clicks on create project (or any athena-exclusive action)
        * Alice is is prompted with message saying that this action requires an athena account and presents her with a big "join athena" button
* Clicks on join athena
    * /join-athena
    * If we can derive public key hash from bech32 address, derive it, otherwise get that from a query parameter
    * Request to athena backend is made for "create-account" transaction (athena should probably be a worker like snapshotter)
    * Return CBOR from athena result
    * (should have some mechanism to avoid spam)
* One of two
    * Signs transaction
        * /confirm/<tx_hash>
        * Profile is updated with transaction state
        * (we need to keep track here of everyu transaction a user is involved in)
    * Declines transaction

### Creating project
As seen in the previous flow, this assumes Alice has already joined athena. Otherwise, when she clicks on the create project button she will be presented with a big "join athena" button.

* Alice lands on main page
* Clicks on projects page
    * /projects (Get projects)
* Clicks on create project button
    * Is redirected to a page where she can fill the project information
    * Fills and submits information
        * /projects/create
        * New project is created and Alice can view and track it on her profile or the projects page

### Starting a Project (or giving up)
After either the deadline Alice has set passed or she received the funding she was asking for, this flow comes in.


* Alice lands on main page
* Accesses her profile
    * /user/<bech32_addr> (Get User Info)
* Clicks on one of her projects
    * /project/<project-id>
* Sees two buttons (start project, give up)
    * Clicks on start project
        * /projects/<project-id>/start
        * Prompted to sign transaction
            * Signs it
                * /confirm/<tx_hash>
                * Can track tx status on her profile
            * Declines it
                * After some minutes if the transaction is not confirmed, it's discarted
    * Clicks on give up
        * /projects/<project-id>/give-up
        * Prompted to sign transaction
            * Signs it
                * /confirm/<tx_hash>
                * Can track tx status on her profile
            * Declines it
                * After some minutes if the transaction is not confirmed, it's discarted

### Complete Deliverable

* Alice lands on main page
* Accesses her profile
    * /user/<bech32_addr> (Get User Info)
* Clicks on one of her projects
    * /project/<project-id>
* Clicks on complete deliverable
    * /projects/<project-id>/<deliverable-id>/complete
    * Prompted to sign transaction
        * Signs it
            * /confirm/<tx_hash>
            * Can track tx status on her profile
        * Declines it
            * After some minutes if the transaction is not confirmed, it's discarted

*Bob*

### Fund Project

* Bob lands on main page
* Access projects page
    * /projects
* Clicks on project he finds interesting
    * /projects/<project-id>
    * Clicks on fund project
        * /projects/<project-id>/fund
        * Prompted to sign transaction
            * Signs it
                * /confirm/<tx_hash>
                * Can track tx status on her profile
            * Declines it
                * After some minutes if the transaction is not confirmed, it's discarted

### Contest deliverable

* Bob lands on page
* Access profile
    * /user/<bech32_addr>
    * Clicks on one of the projects he funded
        * /projects/<project-id>
        * Contests one of the deliverables
            * Prompted to sign transaction
                * Signs it
                    * /confirm/<tx_hash>
                    * Can track tx status on her profile
                * Declines it
                    * After some minutes if the transaction is not confirmed, it's discarted

*Charlie*

### Review Deliverable

* Charlie lands on main page
* Clicks on his profile
    * /user/<bech32_addr>
* One Of
    * Sees that he was selected to mediate a case for a project
        * Clicks on project
            * /projects/<project-id>
    * Sees one pending dispute
* Sees that project has pending deliverable
* One Of 
    * Mark deliverable as completed
        * /projects/<project-id>/<deliverable-id>/confirm
    * Mark deliverable as failed
        * /projects/<project-id>/<deliverable-id>/fail
* Prompted to sign transaction
    * Signs it
        * /confirm/<tx_hash>
        * Can track tx status on her profile
    * Declines it
        * After some minutes if the transaction is not confirmed, it's discarted

## Endpoints

### User
* /user/<bech32_addr> - Get user information

### Athena / Cardano

* /join-athena - Get CBOR of the transaction to create an account in athena
* /confirm/<tx_hash> - Confirm this transaction was submitted

### Projects

* /projects - Get short info of all projects (paginated)
* /projects/create - Create a project to start receiving funds (also get the CBOR of this transaction)
* /projects/<project-id> - Get detailed info of a specific project
* /projects/<project-id>/fund - Fund a project (get the CBOR too)
* /projects/<project-id>/start - Start working on the deliverables for a project (get the CBOR too)
* /projects/<project-id>/give-up - Give up project and give users back their money + collateral as compensation (get CBOR too)
* /projects/<project-id>/<deliverable-id>/complete - Mark deliverable as completed (after review from mediators | also returns CBOR)
* /projects/<project-id>/<deliverable-id>/confirm - Confirm that deliverable was indeed completed
* /projects/<project-id>/<deliverable-id>/fail - Deny that the deliverable was completed

## Notes
Deliverables now should be percentages and not absolute values. This is because a user might want to start a project even though he didn't achieve 100% of the expected funding (specially in the context of the schools). After the set deadline arrives user should chose between start project or give up.