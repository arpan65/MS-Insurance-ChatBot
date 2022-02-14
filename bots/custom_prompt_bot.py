# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# Import necessary libraries
from datetime import datetime
import json
import os
import random
from recognizers_number import recognize_number, Culture
from recognizers_date_time import recognize_datetime

from botbuilder.core import (
    ActivityHandler,
    ConversationState,
    TurnContext,
    UserState,
    MessageFactory,
)
from data_models import ConversationFlow, Question, UserProfile,FileNoteContext
from botbuilder.schema import ChannelAccount, Attachment, Activity, ActivityTypes,CardAction, ActionTypes, SuggestedActions
from botbuilder.core import ActivityHandler, MessageFactory, TurnContext,CardFactory,ConversationState, UserState

CARDS = [
    "resources/FilenoteCard.json",
    "resources/ListCard.json",
    "resources/TaskCard.json"
]

# Class to handle validation
class ValidationResult:
    def __init__(
        self, is_valid: bool = False, value: object = None, message: str = None
    ):
        self.is_valid = is_valid
        self.value = value
        self.message = message

# Main class to handle bot conversion flow
class CustomPromptBot(ActivityHandler):
    def __init__(self, conversation_state: ConversationState, user_state: UserState):
        if conversation_state is None:
            raise TypeError(
                "[CustomPromptBot]: Missing parameter. conversation_state is required but None was given"
            )
        if user_state is None:
            raise TypeError(
                "[CustomPromptBot]: Missing parameter. user_state is required but None was given"
            )

        self.conversation_state = conversation_state
        self.user_state = user_state

        self.flow_accessor = self.conversation_state.create_property("ConversationFlow")
        self.profile_accessor = self.user_state.create_property("UserProfile")

    async def on_members_added_activity(
        self, members_added: [ChannelAccount], turn_context: TurnContext):
        """
        Send a welcome message to the user and tell them what actions they may perform to use this bot
        """
        return await self._send_welcome_message(turn_context)

    async def on_message_activity(self, turn_context: TurnContext):
        # Get the state properties from the turn context.
        profile = await self.profile_accessor.get(turn_context, UserProfile)
        flow = await self.flow_accessor.get(turn_context, ConversationFlow)
        text = turn_context.activity.text.lower()
        await self._fill_out_user_context(flow, profile, turn_context)
        # Save changes to UserState and ConversationState
        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)


    # method to customize initial welcome dialouge 
    async def _send_welcome_message(self, turn_context: TurnContext):
        for member in turn_context.activity.members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    MessageFactory.text(
                        f"Hello, my name is VIA. I can help you to access the assigned claims and take actions from anywhere on the go."
                        f" You can send me a message here."
                    )
                )

                await self._send_suggested_actions(turn_context,is_repeated=False)
    
    # method to send suggested options to choose from
    async def _send_suggested_actions(self, turn_context: TurnContext,is_repeated=False):
        """
        Creates and sends an activity with suggested actions to the user. When the user
        clicks one of the buttons the text value from the "CardAction" will be displayed
        in the channel just as if the user entered the text. There are multiple
        "ActionTypes" that may be used for different situations.
        """
        if is_repeated:
            reply = MessageFactory.text("Anything else I can help you with today?")    
        else:
            reply = MessageFactory.text("How can I help you today?")     
        reply.suggested_actions = SuggestedActions(
        actions=[
        CardAction(
                title="I want to add a FileNote",
                type=ActionTypes.im_back,
                value="Add a File Note"
            ),
        CardAction(
            title="I want to see claim summary",
            type=ActionTypes.im_back,
            value="Show Claim Summary"
        ),
        CardAction(
            title="Show my assigned tasks",
            type=ActionTypes.im_back,
            value="Show My Assigned Tasks"
        ),
        CardAction(
            title="No that's it",
            type=ActionTypes.im_back,
            value="No that's it"
        ),]
        )
        return await turn_context.send_activity(reply)
    
    # method to create adaptive card from filenote data
    def _create_adaptive_card_attachment(self,claimNumber,filenoteText) -> Attachment:
        card_path = os.path.join(os.getcwd(), CARDS[0])
        with open(card_path, "rb") as in_file:
            card_data = json.load(in_file)
        #print(card_data)
        claim_number='Claim Number: '+claimNumber
        filenote_text='**Filenote Text:** '+filenoteText
        filenote_id='Filenote Id: '+str(random.randint(99999,99999999))
        card_data['body'][0]['columns'][0]['items'].append({'type': 'TextBlock','text':filenote_text ,'size': 'small','wrap': True})
        card_data['body'][0]['columns'][0]['items'].append({'type': 'TextBlock', 'text': claim_number})
        card_data['body'][0]['columns'][0]['items'].append({'type': 'TextBlock', 'text': filenote_id})
        return CardFactory.adaptive_card(card_data)
    
    # method to create adaptive cards from tasks
    def _create_tasks_adaptive_card(self) -> Attachment:
        card_path = os.path.join(os.getcwd(), CARDS[2])
        with open(card_path, "rb") as in_file:
            card_data = json.load(in_file)
        return CardFactory.adaptive_card(card_data)

    async def _fill_out_user_context(
        self, flow: ConversationFlow, profile: FileNoteContext, turn_context: TurnContext
    ):
        user_input = turn_context.activity.text.strip()
        
        # ask for claim number
        if flow.last_question_asked == Question.NONE and user_input=="Add a File Note":
            await turn_context.send_activity(
            MessageFactory.text("Let's get started. Can you please enter the claim number?")
            )
            flow.last_question_asked = Question.CLAIMNUMBER

        # validate name then ask for filenote text
        elif flow.last_question_asked == Question.CLAIMNUMBER:
            validate_result = self._validate_claim_number(user_input)
            if not validate_result.is_valid:
                await turn_context.send_activity(
                    MessageFactory.text(validate_result.message)
                )
            else:
                profile.claimNumber = validate_result.value
                await turn_context.send_activity(
                    MessageFactory.text(f"I got the claim number as {profile.claimNumber}")
                )
                await turn_context.send_activity(
                    MessageFactory.text("Please enter the text you want to enter in the filenote")
                )
                flow.last_question_asked = Question.FILENOTETEXT

        # validate the text then create filenote
        elif flow.last_question_asked == Question.FILENOTETEXT:    
            validate_result = self._validate_filenote_text(user_input)
            if not validate_result.is_valid:
                await turn_context.send_activity(
                    MessageFactory.text(validate_result.message)
                )
            else:
                profile.text = validate_result.value
                await turn_context.send_activity(
                    MessageFactory.text(f"I have the text as {profile.text}.")
                )
                await turn_context.send_activity(
                    MessageFactory.text("Please wait while I am creating the file note.")
                )
                message = Activity(
                text="your file note is created sucessfully. Please find the details below",
                type=ActivityTypes.message,
                attachments=[self._create_adaptive_card_attachment(profile.claimNumber,profile.text)],)
                await turn_context.send_activity(message)
                flow.last_question_asked = Question.OTHER
                await self._send_suggested_actions(turn_context,is_repeated=True)
        
        # end the conversation 
        elif flow.last_question_asked == Question.THANKS or user_input=="No that's it":
            await turn_context.send_activity(
                    MessageFactory.text(f"Thank you. Have a great day!")
            )
        # show assigned tasks of the user    
        elif user_input== "Show My Assigned Tasks" :  
            typing_delay=Activity(type='delay',value=300)
            await turn_context.send_activity(typing_delay)
            type_indicator=Activity(type=ActivityTypes.typing)
            await turn_context.send_activity(type_indicator)
            message = Activity(
            text="Please wait while I fetch the information for you",
            delay=300,
            type=ActivityTypes.message,
            attachments=[self._create_tasks_adaptive_card()],)
            await turn_context.send_activity(message)
            await self._send_suggested_actions(turn_context,is_repeated=True)
            flow.last_question_asked = Question.TASK

    def _validate_claim_number(self, user_input: str) -> ValidationResult:
        if not user_input:
            return ValidationResult(
                is_valid=False,
                message="Please enter a claim number that contains at least one character.",
            )

        return ValidationResult(is_valid=True, value=user_input)

    def _validate_filenote_text(self, user_input: str) -> ValidationResult:
        if not user_input:
            return ValidationResult(
                is_valid=False,
                message="Please enter a text that contains at least one character.",
            )

        return ValidationResult(is_valid=True, value=user_input)

    
        
