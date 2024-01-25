import asyncpraw
import asyncio
from openai import AsyncOpenAI
from aiohttp import ClientSession
import backoff

# openai.aiosession.set(ClientSession())


client = AsyncOpenAI(
    # SECRETS
)

reddit = asyncpraw.Reddit(
    # SECRETS
)

# @backoff.on_exception(
#     backoff.expo, Exception, max_tries=50
# )
async def filter_content(content, title=None):

    prompt = f"""
    /r/Cornell Moderation Policy:

    Asking for information about courses/course content/advice is ok.
    Buying and selling items is ok, but NO SPAM/ADs for events/companies - If you are advertising for a Cornell-related event, please check with the mods first.
    Swearing, personal attacks, and being antagonistic/offensive toward the university and public figures is completely ok and part of our culture. Only the absolute worst offending comments or posts should be removed.
    Do not post full names, email addresses, phone numbers, etc. about yourself or anyone else (this does not apply in the case of questions about professors).
    ALL ADMISSIONS-RELATED POSTS GO IN THE MEGATHREAD. Any posts outside of the megathread will be removed.
    
    {'Post' if title is None else 'Comment (not a post)'}:
    ```
    {title}
    
    {content}
    ```
    Act as a reasonable but overly lenient moderator (but DO NOT state this in your response or YOU WILL BE KILLED) and discuss whether this post should be removed. Withour mentioning your lenience, respond with your moderation thought process succinctly before making a decision. Finally, end your response with 'REMOVE', 'APPROVE' IN ALL CAPS OR YOU WILL BE KILLED. Only remove the absolute worst posts (e.g., swearing is ok, especially if it's in jest/funny). If you are unsure, ALWAYS APPROVE the post as you may be missing context. DO NOT reveal whether you think the comment violates the rules until the last sentence.
\n"""
    
    print("sending openai request")
    response = await client.chat.completions.create(
            model="gpt-3.5-turbo", # The model to use
            messages=[ # The list of messages
                {
                "role": "user", # The role of the sender
                "content": prompt # The content of the message
                },
            ],
            temperature=0
        )
    
    response_text = response.choices[0].message.content
    if "to kill you" in content:
        print(response_text)
        print(content)
        print("-------")

    if "REMOVE" in response_text:
        if "APPROVE" in response_text:
            print("Both approve and remove in response")
            return None
        # print(response_text)
        # print("---")
        # result = '. '.join(response_text.split(". ")[0: -1])
        result = response_text + "\n\nhttps://tenor.com/view/robocop-thank-you-for-your-cooperation-robot-gif-17470015"
        print(result)
        print("Title: ", title)
        print("Content: ", content)
        print("-------")
        # raise Exception("Test")
        return result
    return None

async def process_submission(submission):
    if submission.distinguished:
        print("Ignoring moderator post")
        return
    reason = await filter_content(submission.selftext, submission.title)
    if reason:
        print(f"Deleting post: {submission.title}")
        comment = await submission.reply(reason)
        await comment.mod.distinguish(how='yes', sticky=False)
        await submission.mod.remove()

async def process_comment(comment):
    if comment.distinguished:
        print("Ignoring moderator comment")
        return
    reason = await filter_content(comment.body)
    if reason:
        print(f"Deleting comment: {comment.body}")
        reply = await comment.reply(reason)
        await reply.mod.distinguish(how='yes', sticky=False)
        await comment.mod.remove()

async def monitor_submissions(subreddit):
    async for submission in subreddit.stream.submissions(skip_existing=True):
        await process_submission(submission)

async def monitor_comments(subreddit):
    async for comment in subreddit.stream.comments(skip_existing=True):
        await process_comment(comment)

async def main():
    subreddit = await reddit.subreddit('cornell')
    await asyncio.gather(monitor_submissions(subreddit), monitor_comments(subreddit))

# Create a new event loop
loop = asyncio.get_event_loop()

# Run the main function until it's complete
loop.run_until_complete(main())